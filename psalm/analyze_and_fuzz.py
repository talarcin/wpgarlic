import io
import os
import subprocess
import zipfile

import click
import requests
from rich import print


@click.command()
@click.argument("plugin_slug")
@click.option("--version", required=True, help="Plugin version")
def analyze(plugin_slug, version):
    print("Downloading [bold]{0}[/bold] with version [bold]{1}[/bold]".format(plugin_slug, version))
    req = requests.get("https://downloads.wordpress.org/plugin/{0}.{1}.zip".format(plugin_slug, version))

    if req.ok:
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

    subprocess.call(["./bin/run_analysis_then_fuzz"])

analyze()
