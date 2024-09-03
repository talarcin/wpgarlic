import io
import os
import subprocess
import zipfile

import click
import requests
from rich import print


@click.command()
@click.option("--plugin_slug", required=True, prompt="Plugin slug", help="Plugin slug")
@click.option("--version", required=True, prompt="Plugin version", help="Plugin version")
def analyze(plugin_slug, version):
    print("Downloading [bold]{0}[/bold] with version [bold]{1}[/bold]".format(plugin_slug, version))

    # Check if version of plugin is downloadable
    plugin_info_object: dict = requests.get(
        "https://api.wordpress.org/plugins/info/1.2/?action=plugin_information&request[slug]={0}".format(
            plugin_slug)).json()

    if (len(plugin_info_object.keys()) == 1 and "error" in plugin_info_object.keys()) or (
            "versions" in plugin_info_object.keys() and not f"{version}" in plugin_info_object["versions"].keys()):
        print("[red]Couldn't find a download link for [white]{0}[/white] and version [white]{1}[/white].[/red]".format(
            plugin_slug, version))
        exit(1)

    download_link: str = plugin_info_object["versions"].get(version)
    print("Downloading [bold]{0}[/bold] [bold]v{1}[/bold] from {2}".format(plugin_slug, version, download_link))

    req = requests.get(download_link)

    if req.ok:
        open("./wp-plugins/{0}.zip".format(plugin_slug), "wb").write(req.content)
        print("Extracting plugin to [bold]/psalm/plugin[/bold]...")
        with zipfile.ZipFile(io.BytesIO(req.content)) as zf:

            if not os.path.isdir("./psalm/plugin/"):
                os.mkdir("./psalm/plugin/")

            zf.extractall("./psalm/plugin/")
            print("[green]Extraction done[/green]")
            zf.close()
    else:
        print("[red]Failed to download plugin.[/red]")
        print("[red]Please make sure that the [bold white]plugin slug[/bold white] and [bold white]version[/bold "
              "white] are correct.[/red]")
        exit(1)

    print("Installing composer packages...")
    os.chdir("psalm")

    subprocess.call(["composer", "update"])
    subprocess.call(["composer", "install"])
    subprocess.call(["./vendor/bin/psalm", "--init"])
    subprocess.call(["./vendor/bin/psalm-plugin", "enable", "tuncay/psalm-wp-taint"])

    subprocess.call(["./vendor/bin/analyze", "output", "./plugin/"])
    os.chdir("..")
    print("[green bold]Taint analysis finished successfully.[/green bold]")
    print("Starting fuzzer to fuzz plugin [bold]{0}[/bold] from file [bold]{0}.zip[/bold]".format(plugin_slug))
    subprocess.call(["./bin/fuzz_object", "plugin", "./wp-plugins/{0}.zip".format(plugin_slug)])


analyze()
