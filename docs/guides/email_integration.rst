Email Configuration and Integration
===================================

Saleor offers a few ways to set-up your email settings over SMTP servers and relays
through the below environment variables.


``EMAIL_URL``
+++++++++++++

You can set the environment variable ``EMAIL_URL`` to the SMTP URL,
which will contain a straightforward value as shown in below examples.


.. table::

   ==========================================================  ================================================================================
   Description                                                 URL
   ==========================================================  ================================================================================
   GMail with **SSL on**.                                      ``smtp://my.gmail.username@gmail.com:my-password@smtp.gmail.com:465/?ssl=True``
   OVH with **STARTTLS on**.                                   ``smtp://username@example.com:my-password@pro1.mail.ovh.net:587/?tls=True``
   A SMTP server unencrypted.                                  ``smtp://username@example.com:my-password@smtp.example.com:25/``
   ==========================================================  ================================================================================


.. note::

    If you want to use your personal GMail account to send mails,
    you need to `enable access to unknown applications in your Google Account <https://myaccount.google.com/lesssecureapps>`_.


.. warning::

    Always make sure you set-up correctly at least your SPF records, and while on it, your DKIM records as well.
    **Otherwise your production mails will be denied by most mail servers or intercepted by spam filters.**


.. _DEFAULT_FROM_EMAIL:

``DEFAULT_FROM_EMAIL``
++++++++++++++++++++++

You can customize the sender email address by setting the environment variable ``DEFAULT_FROM_EMAIL`` to your desired email address.
You also can customize the sender name by doing as follow ``Example Is Me <your.name@example.com>``.


Sendgrid Integration
--------------------

After you `created your sendgrid application <https://app.sendgrid.com/guide/integrate/langs/smtp>`_,
you need to set the environment variable ``EMAIL_URL`` as below,
but by replacing ``YOUR_API_KEY_HERE`` with your API key.

``smtp://apikey:YOUR_API_KEY_HERE@smtp.sendgrid.com:465/?ssl=True``

Then, set the environment variable ``DEFAULT_FROM_EMAIL`` `as mentioned before <DEFAULT_FROM_EMAIL_>`_.

.. note::

    As it is not in the setup process of sendgrid, if your 'from email' address is your domain,
    you need to make sure you at least correctly set your
    `SPF <https://sendgrid.com/docs/Glossary/spf.html>`_ DNS record and, optionally, set your
    `DKIM <https://sendgrid.com/docs/Glossary/dkim.html>`_ DNS record as well.


Mailgun Integration
-------------------

After you `added your domain in Mailgun and correctly set-up your domain DNS records <https://app.mailgun.com/app/domains/new>`_,
you can set the environment variable ``EMAIL_URL`` as below,
but by replacing everything capitalized, with your data.

``smtp://YOUR_LOGIN_NAME@YOUR_DOMAIN_NAME:YOUR_DEFAULT_MAILGUN_PASSWORD@smtp.mailgun.org:465/?ssl=True``


Example
+++++++

Let's say my domain name is ``smtp.example.com`` and I want to send emails as ``john.doe@smtp.example.com``
and my password is ``my-mailgun-password``.

.. image:: https://i.imgur.com/pdJjBnD.png

I have to set ``EMAIL_URL`` to:

``smtp://john.doe@smtp.example.com:my-mailgun-password@smtp.mailgun.org:465/?ssl=True``



Mailjet Integration
-------------------

After `adding your domain in Mailjet <https://app.mailjet.com/account/sender/domain#create-domain>`_,
you have to set the environment variable ``EMAIL_URL`` as below,
but by replacing everything capitalized, with your data, available at this `URL <https://app.mailjet.com/account/setup>`_.

``smtp://YOUR_MAILJET_USERNAME:YOUR_MAILJET_PASSWORD@in-v3.mailjet.com:587/?tls=True``

Then, set the environment variable ``DEFAULT_FROM_EMAIL`` `as mentioned before <DEFAULT_FROM_EMAIL_>`_.


Amazon SES Integration
----------------------

After having `verified your domain(s) in AWS SES <https://eu-west-1.console.aws.amazon.com/ses/home#verified-senders-domain:>`_,
and set-up DKIM and SPF records, you need to `create your SMTP credentials <https://eu-west-1.console.aws.amazon.com/ses/home#smtp-settings:>`_.

Then, you can use this data to set-up the environment variable ``EMAIL_URL`` as below, by replacing everything capitalized, with your data.

``smtp://YOUR_SMTP_USERNAME:YOUR_SMTP_PASSWORD@email-smtp.YOUR_AWS_SES_REGION.amazonaws.com:587/?tls=True``

Then, set the environment variable ``DEFAULT_FROM_EMAIL`` `as mentioned before <DEFAULT_FROM_EMAIL_>`_.
