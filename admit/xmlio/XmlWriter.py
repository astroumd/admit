""" .. _XML-writer-api:

    XmlWriter --- Converts in-memory ADMIT objects to XML format.
    -------------------------------------------------------------

    This module defines the main XML writer class for ADMIT.
"""
# system imports
import xml.etree.cElementTree as et
import numpy as np
import copy
import textwrap

# ADMIT imports
import admit.util.bdp_types as bt
from admit.util import UtilBase


class XmlWriter(object):
    """ XML Writer class.

        Class for writing out xml instances of both ATs and BDPs.

        Parameters
        ----------

        clss : various
            The class to be written out in XML.

        order : list
            The order items are written in.

        btype : dict
            Dictionary of the data type for each item.

        root : elementtree node
            The root node to attach to.

        keys : list
            A list of the keywords for an AT.
            Default: None.

        Attributes
        ----------
        None
    """
    def __init__(self, clss, order, btype, root, keys=None):
        self.writexml(clss, order, btype, root, keys)

    def write(self, attr, item, btype, root, typ):
        """ Method to write out an individual item to XML

            Parameters
            ----------
            attr : various
                The value of the item to write out

            item : str
                The name of the item to write out

            btype : dict
                Dictionary of the data types for each item

            root : elementtree
                The root node to attach to

            typ : str
                String containing the type of class being written out. Used only
                for error messages

            Returns
            -------
            None
        """
        # if it is a table, line, or image they have their own routines
        # else treat each data type appropriately
        if isinstance(attr, UtilBase):
            field = et.SubElement(root, item)
            if attr._type.upper() == bt.MULTIIMAGE:
                field.set("type", bt.MULTIIMAGE)
                for k, v in attr.mimages.iteritems():
                    self.write(v, bt.IMG, btype, field, v._type)
                return
            field.set("type", attr._type.upper())
            for item in attr._order:
                attrib = getattr(attr, item)
                self.write(attrib, item, btype, field, attr._type)
        elif isinstance(attr, bool):
            if btype[item] != bt.BOOL:
                raise Exception("Improper type for data member %s in %s, it is a %s, but must be a %s" % (item, typ, "BOOL", btype[item]))
            field = et.SubElement(root, item)
            field.set("type", bt.BOOL)
            if attr:
                field.text = "1"
            else:
                field.text = "0"
        elif isinstance(attr, float):
            if btype[item] != bt.FLOAT:
                raise Exception("Improper type for data member %s in %s, it is a %s, but must be a %s" % (item, typ, "FLOAT", btype[item]))
            field = et.SubElement(root, item)
            field.set("type", bt.FLOAT)
            field.text = repr(attr)
        elif isinstance(attr, dict):
            if btype[item] != bt.DICT:
                raise Exception("Improper type for data member %s in %s, it is a %s, but must be a %s" % (item, typ, "DICT", btype[item]))
            nd = []
            st = []
            field = et.SubElement(root, item)
            for k, v in attr.iteritems():
                if isinstance(v, np.ndarray):
                    nd.append(k)
                    attr[k] = np.ndarray.tolist(v)
                elif isinstance(v, set):
                    st.append(k)
                    attr[k] = list(v)
            field.set("type", bt.DICT)
            field.set("ndarray", str(nd))
            field.set("set", str(st))
            temptext = str(attr)
            tt = ""
            tlist = textwrap.wrap(temptext, width=10000)
            for l in tlist:
                tt += l + "\n"
            field.text = tt
        elif isinstance(attr, int):
            if btype[item] != bt.INT:
                raise Exception("Improper type for data member %s in %s, it is a %s, but must be a %s" % (item, typ, "INT", btype[item]))
            field = et.SubElement(root, item)
            field.set("type", bt.INT)
            field.text = str(attr)
        elif isinstance(attr, list):
            if btype[item] != bt.LIST:
                raise Exception("Improper type for data member %s in %s, it is a %s, but must be a %s" % (item, typ, "LIST", btype[item]))
            nd = []
            st = []
            field = et.SubElement(root, item)
            for i in range(0, len(attr)):
                if isinstance(attr[i], np.ndarray):
                    nd.append(i)
                    attr[i] = np.ndarray.tolist(attr[i])
                elif isinstance(attr[i], set):
                    st.append(i)
                    attr[k] = list(attr[i])
            field.set("type", bt.LIST)
            field.set("ndarray", str(nd))
            field.set("set", str(st))
            temptext = str(attr)
            tt = ""
            tlist = textwrap.wrap(temptext, width=10000)
            for l in tlist:
                tt += l + "\n"
            field.text = tt
        elif isinstance(attr, long):
            if btype[item] != bt.LONG:
                raise Exception("Improper type for data member %s in %s, it is a %s, but must be a %s" % (item, typ, "LONG", btype[item]))
            field = et.SubElement(root, item)
            field.set("type", bt.LONG)
            field.text = str(attr)
        elif isinstance(attr, str):
            if btype[item] != bt.STRING:
                raise Exception("Improper type for data member %s in %s, it is a %s, but must be a %s" % (item, typ, "STRING", btype[item]))
            field = et.SubElement(root, item)
            field.set("type", bt.STRING)
            temptext = attr
            tt = ""
            tlist = textwrap.wrap(temptext, width=10000)
            for l in tlist:
                tt += l + "\n"
            field.text = tt
        elif isinstance(attr, tuple):
            if btype[item] != bt.TUPLE:
                raise Exception("Improper type for data member %s in %s, it is a %s, but must be a %s" % (item, typ, "TUPLE", btype[item]))
            nd = []
            st = []
            temp = []
            field = et.SubElement(root, item)
            for i in range(0, len(attr)):
                if isinstance(attr[i], np.ndarray):
                    nd.append(i)
                    temp.append(np.ndarray.tolist(attr[i]))
                elif isinstance(attr[i], set):
                    st.append(i)
                    temp.append(list(attr[i]))
                else:
                    temp.append(attr[i])
            field.set("ndarray", str(nd))
            field.set("set", str(st))
            field.set("type", bt.TUPLE)
            temptext = str(attr)
            tt = ""
            tlist = textwrap.wrap(temptext, width=10000)
            for l in tlist:
                tt += l + "\n"
            field.text = tt
        elif isinstance(attr, np.ndarray):
            if btype[item] != bt.NDARRAY:
                raise Exception("Improper type for data member %s in %s, it is a %s, but must be a %s" % (item, typ, "NDARRAY", btype[item]))
            field = et.SubElement(root, item)
            attr = np.ndarray.tolist(attr)
            field.set("type", bt.NDARRAY)
            temptext = str(attr)
            tt = ""
            tlist = textwrap.wrap(temptext, width=10000)
            for l in tlist:
                tt += l + "\n"
            field.text = tt
        elif isinstance(attr, set):
            if btype[item] != bt.SET:
                raise Exception("Improper type for data member %s in %s, it is a %s, but must be a %s" % (item, typ, "SET", btype[item]))
            attr = list(attr)
            nd = []
            st = []
            field = et.SubElement(root, item)
            for i in range(0, len(attr)):
                if isinstance(attr[i], np.ndarray):
                    nd.append(i)
                    attr[i] = np.ndarray.tolist(attr[i])
                elif isinstance(attr[i], set):
                    st.append(i)
                    attr[k] = list(attr[i])
            field.set("type", bt.SET)
            field.set("ndarray", str(nd))
            field.set("set", str(st))
            temptext = str(attr)
            tt = ""
            tlist = textwrap.wrap(temptext, width=10000)
            for l in tlist:
                tt += l + "\n"
            field.text = tt
        else:
            raise Exception("Unknown type %s encountered for %s" % (type(item), item))

    def writexml(self, clss, order, btype, root, keys):
        """ Method to loop through all data members in the dtd and write them to XML

            Parameters
            ----------
            clss : various
                The class to be written out in XML

            order : list
                The order items are written in

            btype : dict
                Dictionary of the data type for each item

            root : elementtree node
                The root node to attach to

            keys : list
                A list of the keywrods for an AT

            Returns
            -------
            None
        """
        for item in order:
            if item == "_keys":
                continue
            attr = getattr(clss, item)
            self.write(attr, item, btype, root, clss._type)

        if keys is not None:
            keyroot = et.SubElement(root, "_keys")
            keyroot.set("type", bt.DICT)
            tkeys = getattr(clss, "_keys")
            for item in keys:
                attr = tkeys[item]
                self.write(attr, item, btype, keyroot, clss._type)
