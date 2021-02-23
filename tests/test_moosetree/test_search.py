#!/usr/bin/env python3
#* This file is part of MOOSETOOLS repository
#* https://www.github.com/idaholab/moosetools
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moose/blob/master/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import unittest
import moosetree
from .test_iterate import build_tree


class TestSearch(unittest.TestCase):
    def testFindAll(self):
        root = build_tree()
        nodes = list(
            moosetree.findall(root,
                              lambda n: n.name.endswith('AB'),
                              method=moosetree.IterMethod.PRE_ORDER))
        self.assertEqual(len(nodes), 3)
        self.assertEqual(nodes[0].name, 'AB')
        self.assertEqual(nodes[1].name, 'ABCAB')
        self.assertEqual(nodes[2].name, 'BAB')

        nodes = list(
            moosetree.search.findall(root,
                                     lambda n: 'year' in n,
                                     method=moosetree.IterMethod.PRE_ORDER))
        self.assertEqual(len(nodes), 6)
        self.assertEqual(nodes[0].name, 'ABC')
        self.assertEqual(nodes[1].name, 'ABCAB')
        self.assertEqual(nodes[2].name, 'BAB')
        self.assertEqual(nodes[3].name, 'BB')
        self.assertEqual(nodes[4].name, 'C')
        self.assertEqual(nodes[5].name, 'CB')

        self.assertEqual(nodes[0]['year'], 1980)
        self.assertEqual(nodes[1]['year'], 2013)
        self.assertEqual(nodes[2]['year'], 1954)
        self.assertEqual(nodes[3]['year'], 1949)
        self.assertEqual(nodes[4]['year'], 2011)
        self.assertEqual(nodes[5]['year'], 1980)

        nodes = list(
            moosetree.findall(root,
                              lambda n: n.get('year') == 1980,
                              method=moosetree.IterMethod.PRE_ORDER))
        self.assertEqual(len(nodes), 2)
        self.assertIs(nodes[0].name, 'ABC')
        self.assertIs(nodes[1].name, 'CB')

        self.assertEqual(nodes[0]['year'], 1980)
        self.assertEqual(nodes[1]['year'], 1980)

    def testFind(self):
        root = build_tree()
        node = moosetree.find(root, lambda n: n.name.endswith('AB'))
        self.assertEqual(node.name, 'AB')

        node = moosetree.find(root, lambda n: n.name.endswith('not this'))
        self.assertIs(node, None)

        node = moosetree.find(root, lambda n: n.get('year') == 2013)
        self.assertEqual(node.name, 'ABCAB')

    def testFindAttr(self):
        root = build_tree()
        nodes = list(moosetree.findall(root, year=1980))
        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0].name, 'CB')
        self.assertEqual(nodes[1].name, 'ABC')


if __name__ == '__main__':
    unittest.main(verbosity=2)
