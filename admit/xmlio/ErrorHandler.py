""" _ErrorHandler-api:

    ErrorHandler --- Handles errors from the XML parser.
    ----------------------------------------------------

    This module defines the ErrorHandler class.

"""
# system imports
from xml import sax

# ADMIT parser
from admit.util.AdmitLogging import AdmitLogging as logging


class ErrorHandler(sax.handler.ErrorHandler):
    """ Class for handling errors from the parser.

        Parameters
        ----------
        None

        Attributes
        ----------
        None
    """
    def __init__(self):
        pass

    def error(self, ex):
        """ Method called when an error is encountered

            Parameters
            ----------
            ex : exception
                The error that was encountered

            Returns
            -------
            None
        """
        logging.warning("Recoverable error encountered: %s" % (ex.message))

    def fatalError(self, ex):
        """ Method called when a fata error is encountered

            Parameters
            ----------
            ex : exception
                The error encountered

            Returns
            -------
            None
        """
        logging.error("Fatal error encountered.")
        raise ex

    def warning(self, ex):
        """ Method called when the parser issues a warning

            Parameters
            ----------
            ex : exception
                The warning to be issued.

            Returns
            -------
            None
        """
        logging.warning("Warning: %s" % (ex.message))
