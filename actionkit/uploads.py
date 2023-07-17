import sys
import time

from requests_toolbelt import MultipartEncoderMonitor

from .httpmethods import HttpMethods


def progressing(monitor):
    sys.stdout.write(".")


class Uploads(HttpMethods):
    resource_name = 'upload'

    def poll(self, upload_url):
        return self.get(upload_url)

    def upload(self, file_name, import_page):
        m = MultipartEncoderMonitor.from_fields(
            fields={
                'page': import_page,
                'upload': (file_name, open(file_name, 'rb'), 'text/csv'),
                'autocreate_user_fields': 'false',
            },
            callback=progressing,
        )

        upload_url = self.post(data=m, headers={'Content-Type': m.content_type})

        upload = self.poll(upload_url)
        while not upload['is_completed']:
            upload = self.poll(upload_url)
            time.sleep(1)
