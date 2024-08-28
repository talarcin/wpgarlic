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
    req = requests.get("https://downloads.wordpress.org/plugin/{0}.{1}.zip".format(plugin_slug, version))

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
        print("[red]Failed to download plugin.[/red]".format(plugin_slug, version))
        print("[red]Please make sure that the [bold white]plugin slug[/bold white] and [bold white]version[/bold "
              "white] are correct.[/red]")
        exit(1)

    print("Installing composer packages...")
    print(os.getcwd())
    os.chdir("psalm")
    print(os.getcwd())

    subprocess.call(["composer", "update"])
    subprocess.call(["composer", "install"])

    subprocess.call(["./vendor/bin/analyze", "./out/output", "./plugin/"])


analyze()
