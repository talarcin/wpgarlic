import io
import os
import subprocess
import time
import zipfile

import click
import requests
from pygments.lexer import using
from rich import print


@click.command()
@click.option("--plugin_slug", required=True, help="Slug of the plugin")
@click.option("--version", required=True, help="Version number of the plugin")
@click.option("--file", help="Path to .zip file of plugin.")
@click.option("--no_psalm", is_flag=True, default=False, help="Don't use psalm taint analysis")
@click.option("--print_findings", is_flag=True, default=False, help="Print analysis results to file")
@click.option("--reps", default=1, help="Number of fuzzing repetitions")
def analyze(plugin_slug, version, file, no_psalm, print_findings, reps):
    using_file = False
    if file is not None and os.path.isfile("{0}".format(file)):
        print("Found file {0}".format(file))
        print("Using it for the analysis.")
        using_file = True
    elif not os.path.isfile("{0}".format(file)):
        print("No file found under {0}".format(file))

    if not using_file:
        print("Downloading [bold]{0}[/bold] with version [bold]{1}[/bold]".format(plugin_slug, version))
        # Check if version of plugin is downloadable
        plugin_info_object: dict = requests.get(
            "https://api.wordpress.org/plugins/info/1.2/?action=plugin_information&request[slug]={0}".format(
                plugin_slug)).json()

        if (len(plugin_info_object.keys()) == 1 and "error" in plugin_info_object.keys()) or (
                "versions" in plugin_info_object.keys() and not f"{version}" in plugin_info_object["versions"].keys()):
            print("[red]Couldn't find a download link for [white]{0}[/white] and version [white]{1}[/white].[/red]\n"
                  "If you have a .zip file of the plugin check --help to see how to use that instead".format(
                plugin_slug, version))
            exit(1)

        download_link: str = plugin_info_object["versions"].get(version)
        print("Downloading [bold]{0}[/bold] [bold]v{1}[/bold] from {2}".format(plugin_slug, version, download_link))

        req = requests.get(download_link)

        if req.ok:
            if not os.path.isdir("./wp-plugins/"):
                os.mkdir("./wp-plugins/")

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
    else:
        with zipfile.ZipFile("{0}".format(file)) as zf:
            if not os.path.isdir("./psalm/plugin/"):
                os.mkdir("./psalm/plugin/")

            zf.extractall("./psalm/plugin/")
            print("[green]Extraction done[/green]")
            zf.close()

    if not os.path.isdir("./docker_image/psalm-result/"):
        os.mkdir("./docker_image/psalm-result/")

    if not no_psalm:
        print("Installing composer packages...")
        os.chdir("psalm")

        os.system("composer update")
        os.system("composer install")
        subprocess.call(["./vendor/bin/psalm", "--init"])
        subprocess.call(["./vendor/bin/psalm-plugin", "enable", "tuncay/psalm-wp-taint"])

        subprocess.call(["./vendor/bin/analyze", "output", "./plugin/"])
        os.chdir("..")
        print("[green bold]Taint analysis finished successfully.[/green bold]")
        print("\n")
        os.system("rm ./psalm.xml")
        print("Starting fuzzer to fuzz plugin [bold]{0}[/bold] with version {1} from file [bold]{0}.zip[/bold]".format(
            plugin_slug, version))
        print("Copying psalm result files.")
        subprocess.call(["cp", "-r", "./psalm/psalm-result/", "./docker_image/"])
    else:
        if os.path.isfile("./docker_image/psalm-result/actions_to_fuzz-output.json"):
            os.system("rm ./docker_image/psalm-result/actions_to_fuzz-output.json")

    zipfile_path = "./wp-plugins/{0}.zip".format(plugin_slug) if not using_file else file

    while reps >= 1:
        start_time = time.time()
        subprocess.call(["./bin/fuzz_object", "plugin", zipfile_path])
        end_time = time.time()
        elapsed_time = end_time - start_time
        print("[bold]Elapsed time is: [green]{0}s[/green][/bold]".format(str(round(elapsed_time, 2))))
        print("\n")
        reps -= 1

    if print_findings:
        print("Printing findings to {}-{}-findings.txt".format(plugin_slug, version))
        os.system("./bin/print_findings data/object_fuzz_results > {}-{}-findings.txt".format(plugin_slug, version))


analyze()
