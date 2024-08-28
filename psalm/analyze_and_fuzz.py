import io
import os
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
        print("Request ok")
        with zipfile.ZipFile(io.BytesIO(req.content)) as zf:
            is_dir = os.path.isdir("./psalm/plugin/")
            if not is_dir:
                os.mkdir("./psalm/plugin/")
            print("Extracting plugin...")
            zf.extractall("./psalm/plugin/")
            print("Extraction done")
            zf.close()


analyze()
