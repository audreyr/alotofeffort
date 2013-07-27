#!/usr/bin/env python
# -*- coding: utf-8 -*-
import hashlib
import os
import socket

import boto
from boto.s3.key import Key


def deploy_file(root, f, bucket):
    """ Uploads a file to an S3 bucket, as a public file. """

    # Normalize path to remove dot
    # Paths look like:
    #  index.html
    #  css/bootstrap.min.css
    file_path = os.path.normpath(os.path.join(root, f))

    print("Deploying {0}".format(file_path))

    # Upload the actual file to file_path
    k = Key(bucket)    
    k.key = file_path
    try:
        k.set_contents_from_filename(file_path)
        k.set_acl('public-read')
    except socket.error:
        print("Caught socket.error while trying to upload {0}".format(file_path))
        print("Please file an issue with alotofeffort if you see this,")
        print("providing as much info as you can.")
    

def deploy(www_dir, bucket_name):
    """ Deploy to the configured S3 bucket. """

    # Set up the connection to an S3 bucket.
    conn = boto.connect_s3()
    bucket = conn.get_bucket(bucket_name)

    # Deploy each file in www_dir
    os.chdir(www_dir)
    for root, dirs, files in os.walk('.'):
        for f in files:
            deploy_file(root, f, bucket)

    # Make the whole bucket public
    bucket.set_acl('public-read')
    
    # Configure it to be a website
    bucket.configure_website('index.html', 'error.html')
    
    # Print the endpoint, so you know the URL
    print("Your website is now live at {0}".format(bucket.get_website_endpoint()))
    print("If you haven't done so yet, point your domain name there!")


def has_changed_since_last_deploy(file_path, bucket):
    """
    Checks if a file has changed since the last time it was deployed.
    
    :param file_path: Path to file which should be checked. Should be relative
                      from root of bucket.
    :param bucket_name: Name of S3 bucket to check against.
    :returns: True if the file has changed, else False.
    """
    
    print("Checking if {0} has changed since last deploy.".format(file_path))
    with open(file_path) as f:
        data = f.read()
        file_md5 = hashlib.md5(data).hexdigest()
        print("file_md5 is {0}".format(file_md5))
    
    key = bucket.get_key(file_path)

    # HACK: Boto's md5 property does not work when the file hasn't been 
    # downloaded. The etag works but will break for multi-part uploaded files.
    # http://stackoverflow.com/questions/16872679/how-to-programmatically-
    #     get-the-md5-checksum-of-amazon-s3-file-using-boto/17607096#17607096
    # Also the double quotes around it must be stripped. Sketchy...boto's fault
    if key:
        key_md5 = key.etag.replace('"', '').strip()
        print("key_md5 is {0}".format(key_md5))
    else:
        print("File does not exist in bucket")
        return True

    if file_md5 == key_md5:
        print("File has not changed.")
        return False
    print("File has changed.")
    return True