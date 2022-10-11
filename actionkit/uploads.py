from requests_toolbelt import MultipartEncoderMonitor
import sys
import time

def progressing(monitor):
    sys.stdout.write(".")

class Uploads:
    def __init__(self, connection):
        self.connection = connection

    def poll(self, upload_url):
        return self.connection.get(upload_url)

    def upload(self, file_name, import_page):
        m = MultipartEncoderMonitor.from_fields(
            fields={
                'page'  : import_page,
                'upload': (file_name, open(file_name, 'rb'), 'text/csv'),
                'autocreate_user_fields': 'false'
            },
            callback=progressing
        )
        
        url = self.connection._path("upload/")
        response = self.connection.session.post(url, data=m, headers={'Content-Type': m.content_type})
        response.raise_for_status()
        upload_url = response.headers['location']

        upload = self.poll(upload_url)
        while not upload['is_completed']:
            upload = self.poll(upload_url)
            time.sleep(1)
