import warnings

from openid import message as message_module


class Extension(object):
    """An interface for OpenID extensions.

    @ivar ns_uri: The namespace to which to add the arguments for this
        extension
    """
    ns_uri = None
    ns_alias = None

    def getExtensionArgs(self):
        """Get the string arguments that should be added to an OpenID
        message for this extension.

        @returns: A dictionary of completely non-namespaced arguments
            to be added. For example, if the extension's alias is
            'uncle', and this method returns {'meat':'Hot Rats'}, the
            final message will contain {'openid.uncle.meat':'Hot Rats'}
        """
        raise NotImplementedError()

    def toMessage(self, message=None):
        """Add the arguments from this extension to the provided
        message, or create a new message containing only those
        arguments.

        @returns: The message with the extension arguments added
        """
        if message is None:
            warnings.warn(
                'Passing None to Extension.toMessage is deprecated. '
                'Creating a message assuming you want OpenID 2.',
                DeprecationWarning,
                stacklevel=2)
            message = message_module.Message(message_module.OPENID2_NS)

        implicit = message.isOpenID1()

        try:
            message.namespaces.addAlias(
                self.ns_uri, self.ns_alias, implicit=implicit)
        except KeyError:
            if message.namespaces.getAlias(self.ns_uri) != self.ns_alias:
                raise

        message.updateArgs(self.ns_uri, self.getExtensionArgs())
        return message
