from omero.gateway import BlitzGateway
import omero
from omero.rtypes import rstring, rlong, robject, unwrap
import omero.scripts as scripts

import logging
import os
import urllib.parse as urlparse

logger = logging.getLogger('run_ivg_analysis')

def run_script():
    """
    The main entry point of the script, as called by the client via the
    scripting service, passing the required parameters.
    """
    data_types = [rstring('Dataset'), rstring('Image')]

    client = scripts.client(
        'ivg_hpc.py',
        """This script will redirect users to the IVG super-resolution web app.""",

        scripts.String(
            "Token", optional=False, grouping="1",
            description="Please provide a token."),

        scripts.String(
            "Data_Type", optional=True, grouping="2",
            description="Choose source of images.",
            values=data_types, default="Image"),

        scripts.List(
            "IDs", optional=False, grouping="2",
            description="Data ID to process.").ofType(rlong(0)),

        version="0.0.1",
        authors=["Tianyi Miao"],
        institutions=["FNLCR-NIH"],
        contact="tianyi.miao@nih.gov",
    )

    try:
        script_params = client.getInputs(unwrap=True)

        conn = BlitzGateway(client_obj=client)
        username = conn.getUser().getName()

        url = "https://fsivgl-viv01d.ncifcrf.gov/omero/#/?"
        imageIDs = script_params['IDs']
        data_type = script_params['Data_Type']
        token = script_params['Token']

        params = {"data_id": imageIDs[0], "data_type": data_type, "token": token, "username": username}
        url_parse = urlparse.urlparse(url)
        query = url_parse.query
        url_dict = dict(urlparse.parse_qsl(query))
        url_dict.update(params)
        url_new_query = urlparse.urlencode(url_dict)
        url_parse = url_parse._replace(query=url_new_query)
        http_link = urlparse.urlunparse(url_parse)
        client.setOutput(
            "Message",
            rstring("Created button with link to the IVG super-resolution web app."))
        url = omero.rtypes.wrap({
            "type": "URL",
            "href": http_link,
            "title": "Open IVG web App.",
        })
        client.setOutput("URL", url)
    finally:
        client.closeSession()

def main():
    run_script()


if __name__ == "__main__":
    main()