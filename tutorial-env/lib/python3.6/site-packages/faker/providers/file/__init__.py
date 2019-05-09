# coding=utf-8
from __future__ import unicode_literals

import string
from collections import OrderedDict

from .. import BaseProvider


class Provider(BaseProvider):
    application_mime_types = (

        "application/atom+xml",  # Atom feeds
        "application/ecmascript",
        # ECMAScript/JavaScript; Defined in RFC 4329 (equivalent to
        # application/javascript but with stricter processing rules)
        "application/EDI-X12",  # EDI X12 data; Defined in RFC 1767
        "application/EDIFACT",  # EDI EDIFACT data; Defined in RFC 1767
        "application/json",  # JavaScript Object Notation JSON; Defined in RFC 4627
        # ECMAScript/JavaScript; Defined in RFC 4329 (equivalent to
        # application/ecmascript
        "application/javascript",
        #   but with looser processing rules) It is not accepted in IE 8
        #   or earlier - text/javascript is accepted but it is defined as obsolete in RFC 4329.
        #   The "type" attribute of the <script> tag in HTML5 is optional and in practice
        #   omitting the media type of JavaScript programs is the most interoperable
        #   solution since all browsers have always assumed the correct
        #   default even before HTML5.
        "application/octet-stream",
        # Arbitrary binary data.[6] Generally speaking this type identifies files that are not associated with
        # a specific application. Contrary to past assumptions by software packages such as Apache this is not
        # a type that should be applied to unknown files. In such a case, a server or application should not indicate
        # a content type, as it may be incorrect, but rather, should omit the type in order to allow the recipient
        # to guess the type.[7]
        "application/ogg",  # Ogg, a multimedia bitstream container format; Defined in RFC 5334
        "application/pdf",  # Portable Document Format, PDF has been in use for document exchange
        #   on the Internet since 1993; Defined in RFC 3778
        "application/postscript",  # PostScript; Defined in RFC 2046
        "application/rdf+xml",  # Resource Description Framework; Defined by RFC 3870
        "application/rss+xml",  # RSS feeds
        "application/soap+xml",  # SOAP; Defined by RFC 3902
        # Web Open Font Format; (candidate recommendation; use application/x-font-woff
        "application/font-woff",
        #   until standard is official)
        "application/xhtml+xml",  # XHTML; Defined by RFC 3236
        "application/xml-dtd",  # DTD files; Defined by RFC 3023
        "application/xop+xml",  # XOP
        "application/zip",  # ZIP archive files; Registered[8]
        "application/gzip",         # Gzip, Defined in RFC 6713
    )

    audio_mime_types = (
        "audio/basic",  # mulaw audio at 8 kHz, 1 channel; Defined in RFC 2046
        "audio/L24",  # 24bit Linear PCM audio at 8-48 kHz, 1-N channels; Defined in RFC 3190
        "audio/mp4",  # MP4 audio
        "audio/mpeg",  # MP3 or other MPEG audio; Defined in RFC 3003
        "audio/ogg",  # Ogg Vorbis, Speex, Flac and other audio; Defined in RFC 5334
        "audio/vorbis",  # Vorbis encoded audio; Defined in RFC 5215
        # RealAudio; Documented in RealPlayer Help[9]
        "audio/vnd.rn-realaudio",
        "audio/vnd.wave",  # WAV audio; Defined in RFC 2361
        "audio/webm",               # WebM open media format
    )

    image_mime_types = (
        "image/gif",  # GIF image; Defined in RFC 2045 and RFC 2046
        "image/jpeg",  # JPEG JFIF image; Defined in RFC 2045 and RFC 2046
        "image/pjpeg",
        # JPEG JFIF image; Associated with Internet Explorer; Listed in ms775147(v=vs.85) - Progressive JPEG,
        # initiated before global browser support for progressive JPEGs (Microsoft and Firefox).
        # Portable Network Graphics; Registered,[10] Defined in RFC 2083
        "image/png",
        "image/svg+xml",  # SVG vector image; Defined in SVG Tiny 1.2 Specification Appendix M
        # Tag Image File Format (only for Baseline TIFF); Defined in RFC 3302
        "image/tiff",
        "image/vnd.microsoft.icon",  # ICO image; Registered[11]
    )

    message_mime_types = (
        "message/http",  # Defined in RFC 2616
        "message/imdn+xml",  # IMDN Instant Message Disposition Notification; Defined in RFC 5438
        "message/partial",  # Email; Defined in RFC 2045 and RFC 2046
        # Email; EML files, MIME files, MHT files, MHTML files; Defined in RFC
        # 2045 and RFC 2046
        "message/rfc822",
    )

    model_mime_types = (
        "model/example",  # Defined in RFC 4735
        "model/iges",  # IGS files, IGES files; Defined in RFC 2077
        "model/mesh",  # MSH files, MESH files; Defined in RFC 2077, SILO files
        "model/vrml",  # WRL files, VRML files; Defined in RFC 2077
        # X3D ISO standard for representing 3D computer graphics, X3DB binary
        # files
        "model/x3d+binary",
        "model/x3d+vrml",  # X3D ISO standard for representing 3D computer graphics, X3DV VRML files
        "model/x3d+xml",  # X3D ISO standard for representing 3D computer graphics, X3D XML files
    )

    multipart_mime_types = (
        "multipart/mixed",  # MIME Email; Defined in RFC 2045 and RFC 2046
        "multipart/alternative",  # MIME Email; Defined in RFC 2045 and RFC 2046
        # MIME Email; Defined in RFC 2387 and used by MHTML (HTML mail)
        "multipart/related",
        "multipart/form-data",  # MIME Webform; Defined in RFC 2388
        "multipart/signed",  # Defined in RFC 1847
        "multipart/encrypted",  # Defined in RFC 1847
    )

    text_mime_types = (
        "text/cmd",  # commands; subtype resident in Gecko browsers like Firefox 3.5
        "text/css",  # Cascading Style Sheets; Defined in RFC 2318
        "text/csv",  # Comma-separated values; Defined in RFC 4180
        "text/html",  # HTML; Defined in RFC 2854
        "text/javascript",
        # (Obsolete): JavaScript; Defined in and obsoleted by RFC 4329 in order to discourage its usage in favor of
        # application/javascript. However, text/javascript is allowed in HTML 4 and 5 and, unlike
        # application/javascript, has cross-browser support. The "type" attribute of the <script> tag in HTML5 is
        # optional and there is no need to use it at all since all browsers have always assumed the correct default
        # (even in HTML 4 where it was required by the specification).
        "text/plain",  # Textual data; Defined in RFC 2046 and RFC 3676
        "text/vcard",  # vCard (contact information); Defined in RFC 6350
        "text/xml",  # Extensible Markup Language; Defined in RFC 3023
    )

    video_mime_types = (
        "video/mpeg",  # MPEG-1 video with multiplexed audio; Defined in RFC 2045 and RFC 2046
        "video/mp4",  # MP4 video; Defined in RFC 4337
        # Ogg Theora or other video (with audio); Defined in RFC 5334
        "video/ogg",
        "video/quicktime",  # QuickTime video; Registered[12]
        "video/webm",  # WebM Matroska-based open media format
        "video/x-matroska",  # Matroska open media format
        "video/x-ms-wmv",  # Windows Media Video; Documented in Microsoft KB 288102
        "video/x-flv",  # Flash video (FLV files)
    )

    mime_types = OrderedDict((
        ('application', application_mime_types),
        ('audio', audio_mime_types),
        ('image', image_mime_types),
        ('message', message_mime_types),
        ('model', model_mime_types),
        ('multipart', multipart_mime_types),
        ('text', text_mime_types),
        ('video', video_mime_types),
    ))

    audio_file_extensions = (
        "flac",
        "mp3",
        "wav",
    )

    image_file_extensions = (
        "bmp",
        "gif",
        "jpeg",
        "jpg",
        "png",
        "tiff",
    )

    text_file_extensions = (
        "css",
        "csv",
        "html",
        "js",
        "json",
        "txt",
    )

    video_file_extensions = (
        "mp4",
        "avi",
        "mov",
        "webm",
    )

    office_file_extensions = (
        "doc",  # legacy MS Word
        "docx",  # MS Word
        "xls",  # legacy MS Excel
        "xlsx",  # MS Excel
        "ppt",  # legacy MS PowerPoint
        "pptx",  # MS PowerPoint
        "odt",  # LibreOffice document
        "ods",  # LibreOffice spreadsheet
        "odp",  # LibreOffice presentation
        "pages",  # Apple Pages
        "numbers",  # Apple Numbers
        "key",  # Apple Keynote
        "pdf",  # Portable Document Format
    )

    file_extensions = OrderedDict((
        ("audio", audio_file_extensions),
        ("image", image_file_extensions),
        ("office", office_file_extensions),
        ("text", text_file_extensions),
        ("video", video_file_extensions),
    ))
    unix_device_prefixes = ('sd', 'vd', 'xvd')

    def mime_type(self, category=None):
        """
        :param category: application|audio|image|message|model|multipart|text|video
        """
        category = category if category else self.random_element(
            list(self.mime_types.keys()))
        return self.random_element(self.mime_types[category])

    def file_name(self, category=None, extension=None):
        """
        :param category: audio|image|office|text|video
        :param extension: file extension
        """
        extension = extension if extension else self.file_extension(category)
        filename = self.generator.word()
        return '{0}.{1}'.format(filename, extension)

    def file_extension(self, category=None):
        """
        :param category: audio|image|office|text|video
        """
        category = category if category else self.random_element(
            list(self.file_extensions.keys()))
        return self.random_element(self.file_extensions[category])

    def file_path(self, depth=1, category=None, extension=None):
        """
        :param category: audio|image|office|text|video
        :param extension: file extension
        :param depth: depth of the file (depth >= 0)
        """
        file = self.file_name(category, extension)
        path = "/{0}".format(file)
        for _ in range(0, depth):
            path = "/{0}{1}".format(self.generator.word(), path)
        return path

    def unix_device(self, prefix=None):
        """
        :param prefix: sd|vd|xvd
        """
        prefix = prefix or self.random_element(self.unix_device_prefixes)
        suffix = self.random_element(string.ascii_lowercase)
        path = '/dev/%s%s' % (prefix, suffix)
        return path

    def unix_partition(self, prefix=None):
        """
        :param prefix: sd|vd|xvd
        """
        path = self.unix_device(prefix=prefix)
        path += str(self.random_digit())
        return path
