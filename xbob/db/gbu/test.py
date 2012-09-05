#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# @author: Manuel Guenther <Manuel.Guenther@idiap.ch>
# @date:   Fri May 11 17:20:46 CEST 2012
#
# Copyright (C) 2011-2012 Idiap Research Institute, Martigny, Switzerland
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Sanity checks for the GBU database.
"""

import os, sys
import random
import unittest
import bob

from . import Database, models

class GBUDatabaseTest(unittest.TestCase):
  """Performs some tests on the GBU database."""

  def test_clients(self):
    """Tests that the 'clients()' and 'models()' functions return the desired number of elements"""
    db = Database()

    # the protocols training, dev, idiap
    subworlds = models.Trainset.m_names
    protocols = models.Protocol.m_names

    # client counter
    self.assertEqual(len(db.clients()), 782)
    self.assertEqual(len(db.clients(groups='world')), 345)
    for subworld in subworlds:
      self.assertEqual(len(db.clients(groups='world', subworld=subworld)), 345)

    self.assertEqual(len(db.clients(groups='dev')), 437)
    for protocol in protocols:
      self.assertEqual(len(db.clients(groups='dev', protocol=protocol)), 437)

    # model counter
    self.assertEqual(len(db.models(type='gbu', groups='world')), 2128)
    self.assertEqual(len(db.models(type='multi', groups='world')), 345)
    self.assertEqual(len(db.models(type='gbu', groups='dev')), 3255)
    self.assertEqual(len(db.models(type='multi', groups='dev')), 437)
    for subworld in subworlds:
      self.assertEqual(len(db.models(type='multi', groups='world', subworld=subworld)), 345)
    for protocol in protocols:
      self.assertEqual(len(db.models(type='gbu', groups='dev', protocol=protocol)), 1085)
      self.assertEqual(len(db.models(type='multi', groups='dev', protocol=protocol)), 437)

    for protocol in protocols:
      # assert that all models of the 'gbu' protocol type
      #  start with "nd1R" or "nd2R", i.e., the file id
      for model in db.models(type='gbu', protocol=protocol):
        base = os.path.basename(model)
        self.assertTrue(base[:2] == 'nd' and base[3] == 'R')
      # assert that all models of the 'multi' protocol type
      #  start with "nd1S", i.e., the client id
      for model in db.models(type='multi', protocol=protocol):
        self.assertTrue('nd1S' in model)


  def test_files(self):
    """Tests that the 'files()' function returns reasonable output"""
    db = Database()

    # the training subworlds and the protocols
    subworlds = models.Trainset.m_names
    protocols = models.Protocol.m_names

    # check that the number of models is identical to the number of files
    # when 'gbu' protocol types are used
    for subworld in subworlds:
      self.assertEqual(len(db.files(groups='world', subworld=subworld)),
                       len(db.models(type='gbu', groups='world', subworld=subworld)))

    for protocol in protocols:
      # The number of files for each purpose is equal to the number of models
      self.assertEqual(len(db.files(groups='dev', protocol=protocol, purposes='enrol')),
                       len(db.models(type='gbu', groups='dev', protocol=protocol)))
      self.assertEqual(len(db.files(groups='dev', protocol=protocol, purposes='probe')),
                       len(db.models(type='gbu', groups='dev', protocol=protocol)))

    # The following tests might take a while...
    protocol = protocols[0]
    probe_file_count = len(db.files(type='gbu', groups='dev', protocol=protocol, purposes='probe'))
    # check that for 'gbu' protocol types, exactly one file per id is returned
    for model_id in random.sample(db.models(type='gbu', groups='dev', protocol=protocol), 10):
      # assert that there is exactly one file for each enrol purposes per model
      self.assertEqual(len(db.files(type='gbu', groups='dev', protocol=protocol, model_ids=[model_id], purposes='enrol')), 1)
      # probe files should always be the same
      self.assertEqual(len(db.files(type='gbu', groups='dev', protocol=protocol, model_ids=[model_id], purposes='probe')), probe_file_count)

    # for the 'multi' protocols, there is AT LEAST one file per model
    for model_id in random.sample(db.models(type='multi', groups='dev', protocol=protocol), 10):
      # assert that there is exactly one file for each enrol purposes per model
      self.assertTrue(len(db.files(type='multi', groups='dev', protocol=protocol, model_ids=[model_id], purposes='enrol')) >= 1)
      # probe files should always be the same
      self.assertEqual(len(db.files(type='multi', groups='dev', protocol=protocol, model_ids=[model_id], purposes='probe')), probe_file_count)


  def test_file_ids(self):
    """Tests that the client id's returned by the 'get_client_id_from_file_id()' and 'get_client_id_from_model_id()' functions are correct"""
    db = Database()

    # the training subworlds and the protocols
    protocol = models.Protocol.m_names[0]

    # for 'gbu' protocols, get_client_id_from_file_id and get_client_id_from_model_id should return the same value
    for model_id in random.sample(db.models(type='gbu', groups='dev', protocol=protocol), 10):
      for file_id in db.files(type='gbu', groups='dev', protocol=protocol, model_ids=[model_id], purposes='enrol'):
        self.assertEqual(
              db.get_client_id_from_file_id(file_id),
              db.get_client_id_from_model_id(model_id, type='gbu'))

    for model_id in random.sample(db.models(type='multi', groups='dev', protocol=protocol), 10):
      # for 'multi' protocols, get_client_id_from_model_id should return the client id.
      self.assertEqual(db.get_client_id_from_model_id(model_id, type='multi'), model_id)
      # and also get_client_id_from_file_id should return the model id, both for enrol and probe sets
      for file_id in db.files(type='multi', groups='dev', protocol=protocol, model_ids=[model_id], purposes='enrol'):
        self.assertEqual(db.get_client_id_from_file_id(file_id), model_id)

  def test_driver_api(self):
    from bob.db.script.dbmanage import main
    self.assertEqual( main(['gbu', 'dumplist', '--self-test']), 0 )
    self.assertEqual( main(['gbu', 'checkfiles', '-d', '.', '--self-test']), 0 )
    self.assertEqual( main(['gbu', 'create-annotation-files', '-d', '.', '--self-test']), 0 )

