from communication.mail import SUBJECT, TEXT, HTML, send_email, render_blocks

from mock import Mock, patch, sentinel
from unittest2 import TestCase

from django.template.loader_tags import BlockNode


class SendEmailTestCase(TestCase):

    def setUp(self):
        patcher = patch('communication.mail.settings')
        self.settings_mock = patcher.start()
        patcher = patch('communication.mail.render_blocks')
        self.render_mock = patcher.start()
        patcher = patch('communication.mail.EmailMultiAlternatives')
        self.email_mock = patcher.start()

        self.settings_mock.DEFAULT_FROM_EMAIL = sentinel.from_email

    def test_sending_email_without_html(self):
        """Html content is not attached when html block is missing"""
        self.render_mock.return_value = {SUBJECT: sentinel.subject,
                                         TEXT: sentinel.text}
        send_email(address=sentinel.address,
                   template_name=sentinel.template_name,
                   context=sentinel.context)
        self.assert_email_constructed()
        self.email_mock().send.assert_called_once()

    def test_sending_email_with_html(self):
        """Html content is attached when html block present"""
        self.render_mock.return_value = {SUBJECT: sentinel.subject,
                                         TEXT: sentinel.text,
                                         HTML: sentinel.html}
        send_email(address=sentinel.address,
                   template_name=sentinel.template_name,
                   context=sentinel.context)
        self.assert_email_constructed()
        self.email_mock().attach_alternative.assert_called_once_with(
            sentinel.html, 'text/html')
        self.email_mock().send.assert_called_once()

    def assert_email_constructed(self):
        self.email_mock.assert_called_once_with(
            subject=sentinel.subject,
            body=sentinel.text,
            from_email=sentinel.from_email,
            to=[sentinel.address])

    def tearDown(self):
        patch.stopall()


class RenderBlocksTestCase(TestCase):

    @patch('communication.mail.get_template')
    @patch('communication.mail.Context')
    def test_block_rendering(self, context_mock, get_template_mock):
        """Template blocks are rendered with proper context"""
        html_block = Mock(spec=BlockNode)
        html_block.name = HTML
        some_block = Mock(spec=BlockNode)
        some_block.name = 'some_block'
        non_block = Mock()
        get_template_mock.return_value = [html_block, some_block, non_block]
        blocks = render_blocks(template_name=sentinel.template_name,
                               context=sentinel.context)
        self.assertEquals(blocks, {HTML: html_block.render()})
        context_mock.assert_called_once_with(sentinel.context)
