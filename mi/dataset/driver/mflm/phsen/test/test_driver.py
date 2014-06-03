"""
@package mi.dataset.driver.mflm.phsen.test.test_driver
@file marine-integrations/mi/dataset/driver/mflm/phsen/driver.py
@author Emily Hahn
@brief Test cases for mflm_phsen driver

USAGE:
 Make tests verbose and provide stdout
   * From the IDK
       $ bin/dsa/test_driver
       $ bin/dsa/test_driver -i [-t testname]
       $ bin/dsa/test_driver -q [-t testname]
"""

__author__ = 'Emily Hahn'
__license__ = 'Apache 2.0'

import unittest
import os
import shutil
from nose.plugins.attrib import attr
from mock import Mock

from pyon.agent.agent import ResourceAgentState
from interface.objects import ResourceAgentErrorEvent
from interface.objects import ResourceAgentConnectionLostErrorEvent

from mi.core.log import get_logger ; log = get_logger()
from mi.core.instrument.instrument_driver import DriverEvent
from mi.idk.exceptions import SampleTimeout
from mi.idk.dataset.unit_test import DataSetTestCase
from mi.idk.dataset.unit_test import DataSetIntegrationTestCase
from mi.idk.dataset.unit_test import DataSetQualificationTestCase
from mi.dataset.dataset_driver import DataSourceConfigKey, DataSetDriverConfigKeys
from mi.dataset.dataset_driver import DriverParameter, DriverStateKey

from mi.dataset.driver.mflm.phsen.driver import MflmPHSENDataSetDriver
from mi.dataset.parser.phsen import PhsenParserDataParticle, PhsenControlDataParticle
from mi.dataset.parser.phsen import DataParticleType


# Fill in driver details
DataSetTestCase.initialize(
    driver_module='mi.dataset.driver.mflm.phsen.driver',
    driver_class='MflmPHSENDataSetDriver',
    agent_resource_id = '123xyz',
    agent_name = 'Agent007',
    agent_packet_config = MflmPHSENDataSetDriver.stream_config(),
    startup_config = {
        DataSourceConfigKey.HARVESTER:
        {
            DataSetDriverConfigKeys.DIRECTORY: '/tmp/dsatest',
            DataSetDriverConfigKeys.PATTERN: 'node59p1.dat',
            DataSetDriverConfigKeys.FREQUENCY: 1,
            DataSetDriverConfigKeys.FILE_MOD_WAIT_TIME: 2,
        },
        DataSourceConfigKey.PARSER: {}
    }
)

SAMPLE_STREAM = 'phsen_abcdef_sio_mule_instrument'

###############################################################################
#                            INTEGRATION TESTS                                #
# Device specific integration tests are for                                   #
# testing device specific capabilities                                        #
###############################################################################
@attr('INT', group='mi')
class IntegrationTest(DataSetIntegrationTestCase):

    def test_get(self):
        """
        Test that we can get data from files.  Verify that the driver
        sampling can be started and stopped
        """
        # Start sampling
        self.driver.start_sampling()

        self.create_sample_data("node59p1_step1.dat", "node59p1.dat", copy_metadata=False)
        self.assert_data((PhsenParserDataParticle,PhsenControlDataParticle),
            'test_data_1.txt.result.yml', count=2)

        # there is only one file we read from, this example 'appends' data to
        # the end of the node59p1.dat file, and the data from the new append
        # is returned (not including the original data from _step1)
        self.create_sample_data("node59p1_step2.dat", "node59p1.dat", copy_metadata=False)
        self.assert_data(PhsenParserDataParticle, 'test_data_2.txt.result.yml',
                         count=2)

        # now 'appends' the rest of the data and just check if we get the right number
        self.create_sample_data("node59p1_step4.dat", "node59p1.dat", copy_metadata=False)
        self.assert_data(PhsenParserDataParticle, count=6)

    def test_harvester_new_file_exception(self):
        """
        Test an exception raised after the driver is started during
        the file read.  Should call the exception callback.
        """

        # create the file so that it is unreadable
        self.create_sample_data("node59p1_step1.dat", "node59p1.dat", mode=000)

        # Start sampling and watch for an exception
        self.driver.start_sampling()

        self.assert_exception(ValueError)

        # At this point the harvester thread is dead.  The agent
        # exception handle should handle this case.

    def test_stop_resume(self):
        """
        Test the ability to stop and restart the process
        """
        self.create_sample_data("node59p1_step1.dat", "node59p1.dat", copy_metadata=False)
        driver_config = self._driver_config()['startup_config']
        fullfile = os.path.join(driver_config['harvester']['directory'],
                            driver_config['harvester']['pattern'])
        mod_time = os.path.getmtime(fullfile)

        # Create and store the new driver state
        self.memento = {"node59p1.dat": {DriverStateKey.FILE_SIZE: 911,
                        DriverStateKey.FILE_CHECKSUM: '8b7cf73895eded0198b3f3621f962abc',
                        DriverStateKey.FILE_MOD_DATE: mod_time,
                        DriverStateKey.PARSER_STATE: {'in_process_data': [],
                                                     'unprocessed_data':[[0, 172]]}
                        }}

        self.driver = MflmPHSENDataSetDriver(
            self._driver_config()['startup_config'],
            self.memento,
            self.data_callback,
            self.state_callback,
            self.event_callback,
            self.exception_callback)

        # create some data to parse
        self.clear_async_data()
        self.create_sample_data("node59p1_step2.dat", "node59p1.dat", copy_metadata=False)

        self.driver.start_sampling()

        # verify data is produced
        self.assert_data(PhsenParserDataParticle, 'test_data_2.txt.result.yml',
                         count=2, timeout=10)

    def test_back_fill(self):
        """
        Test that a file with a zeroed block of data is read, skipping the zeroed block, then
        when that block is replaced with data, that record is returned
        """
        self.driver.start_sampling()

        # step 2 contains 3 blocks (4 records), start with this and get both since we used them
        # separately in other tests
        self.create_sample_data("node59p1_step2.dat", "node59p1.dat", copy_metadata=False)
        self.assert_data((PhsenParserDataParticle,PhsenControlDataParticle),
            'test_data_1-2.txt.result.yml', count=4)

        # This file has had a section of data replaced with 0s (14171-14675),
        # replacing PH1236501_01D6u51F11341_5D_E538
        self.create_sample_data('node59p1_step3.dat', "node59p1.dat", copy_metadata=False)
        self.assert_data(PhsenParserDataParticle, 'test_data_3.txt.result.yml',
                         count=5)

        # Now fill in the zeroed section from step3, this should just return the new
        # data 
        self.create_sample_data('node59p1_step4.dat', "node59p1.dat", copy_metadata=False)
        self.assert_data(PhsenParserDataParticle, 'test_data_4.txt.result.yml',
                         count=1)

        # start over now using step 4
        self.driver.stop_sampling()
        # Reset the driver with no memento
        self.driver = self._get_driver_object(memento=None)
        self.driver.start_sampling()

        self.clear_async_data()
        self.create_sample_data('node59p1_step4.dat', "node59p1.dat", copy_metadata=False)
        self.assert_data((PhsenParserDataParticle,PhsenControlDataParticle),
            'test_data_1-4.txt.result.yml', count=10)

###############################################################################
#                            QUALIFICATION TESTS                              #
# Device specific qualification tests are for                                 #
# testing device specific capabilities                                        #
###############################################################################
@attr('QUAL', group='mi')
class QualificationTest(DataSetQualificationTestCase):

    def test_harvester_new_file_exception(self):
        """
        Test an exception raised after the driver is started during
        the file read.

        exception callback called.
        """
        # need to put data in the file, not just make an empty file for this to work
        self.create_sample_data('node59p1_step4.dat', "node59p1.dat", mode=000)

        self.assert_initialize(final_state=ResourceAgentState.COMMAND)

        self.event_subscribers.clear_events()
        self.assert_resource_command(DriverEvent.START_AUTOSAMPLE)
        self.assert_state_change(ResourceAgentState.LOST_CONNECTION, 90)
        self.assert_event_received(ResourceAgentConnectionLostErrorEvent, 10)

        self.create_sample_data('node59p1_step4.dat', "node59p1.dat")

        # Should automatically retry connect and transition to streaming
        self.assert_state_change(ResourceAgentState.STREAMING, 90)

    def test_publish_path(self):
        """
        Setup an agent/driver/harvester/parser and verify that data is
        published out the agent
        """

        self.create_sample_data('node59p1_step1.dat', "node59p1.dat")

        self.assert_initialize()

        try:
            # Verify we get one sample
            result = self.data_subscribers.get_samples(DataParticleType.CONTROL, 1)
            result1 = self.data_subscribers.get_samples(DataParticleType.SAMPLE, 1)
            result.extend(result1)
            log.info("RESULT: %s", result)

            # Verify values
            self.assert_data_values(result, 'test_data_1.txt.result.yml')
        except Exception as e:
            log.error("Exception trapped: %s", e)
            self.fail("Sample timeout.")

    def test_large_import(self):
        """
        Test importing a large number of samples from the file at once
        """
        self.create_sample_data('node59p1.dat')
        self.assert_initialize()

        result = self.data_subscribers.get_samples(DataParticleType.CONTROL, 1, 60)
        result = self.data_subscribers.get_samples(DataParticleType.SAMPLE, 200, 360)

    def test_stop_start(self):
        """
        Test the agents ability to start data flowing, stop, then restart
        at the correct spot.
        """
        log.info("CONFIG: %s", self._agent_config())
        self.create_sample_data('node59p1_step2.dat', "node59p1.dat")

        self.assert_initialize(final_state=ResourceAgentState.COMMAND)

        # Slow down processing to 1 per second to give us time to stop
        self.dataset_agent_client.set_resource({DriverParameter.RECORDS_PER_SECOND: 1})
        self.assert_start_sampling()

        # Verify we get one sample
        try:
            # Read the first file and verify the data
            result = self.data_subscribers.get_samples(DataParticleType.CONTROL, 1)
            result1 = self.data_subscribers.get_samples(DataParticleType.SAMPLE, 3)
            result.extend(result1)
            log.debug("RESULT: %s", result)

            # Verify values
            self.assert_data_values(result, 'test_data_1-2.txt.result.yml')
            self.assert_sample_queue_size(DataParticleType.CONTROL, 0)
            self.assert_sample_queue_size(DataParticleType.SAMPLE, 0)

            self.create_sample_data('node59p1_step4.dat', "node59p1.dat")
            # Now read the first record of the second file then stop
            result = self.data_subscribers.get_samples(DataParticleType.SAMPLE, 3)
            log.debug("RESULT 1: %s", result)
            self.assert_stop_sampling()
            self.assert_sample_queue_size(DataParticleType.CONTROL, 0)
            self.assert_sample_queue_size(DataParticleType.SAMPLE, 0)

            # Restart sampling and ensure we get the last records of the file
            self.assert_start_sampling()
            result2 = self.data_subscribers.get_samples(DataParticleType.SAMPLE, 3)
            log.debug("RESULT 2: %s", result2)
            result.extend(result2)
            log.debug("RESULT: %s", result)
            self.assert_data_values(result, 'test_data_3-4.txt.result.yml')
            self.assert_sample_queue_size(DataParticleType.CONTROL, 0)
            self.assert_sample_queue_size(DataParticleType.SAMPLE, 0)
        except SampleTimeout as e:
            log.error("Exception trapped: %s", e, exc_info=True)
            self.fail("Sample timeout.")

    def test_shutdown_restart(self):
        """
        Test a full stop of the dataset agent, then restart the agent and
        confirm it restarts at the correct spot.
        """
        log.info("CONFIG: %s", self._agent_config())
        self.create_sample_data('node59p1_step2.dat', "node59p1.dat")

        self.assert_initialize(final_state=ResourceAgentState.COMMAND)

        # Slow down processing to 1 per second to give us time to stop
        self.dataset_agent_client.set_resource({DriverParameter.RECORDS_PER_SECOND: 1})
        self.assert_start_sampling()

        # Verify we get one sample
        try:
            # Read the first file and verify the data
            result = self.data_subscribers.get_samples(DataParticleType.CONTROL, 1)
            result1 = self.data_subscribers.get_samples(DataParticleType.SAMPLE, 3)
            result.extend(result1)
            log.debug("RESULT: %s", result)

            # Verify values
            self.assert_data_values(result, 'test_data_1-2.txt.result.yml')
            self.assert_sample_queue_size(DataParticleType.CONTROL, 0)
            self.assert_sample_queue_size(DataParticleType.SAMPLE, 0)

            self.create_sample_data('node59p1_step4.dat', "node59p1.dat")
            # Now read the first record of the second file then stop
            result = self.data_subscribers.get_samples(DataParticleType.SAMPLE, 3)
            log.debug("RESULT 1: %s", result)
            self.assert_stop_sampling()
            self.assert_sample_queue_size(DataParticleType.CONTROL, 0)
            self.assert_sample_queue_size(DataParticleType.SAMPLE, 0)

            # stop and re-start the agent
            self.stop_dataset_agent_client()
            self.init_dataset_agent_client()
            # re-initialize
            self.assert_initialize()

            result2 = self.data_subscribers.get_samples(DataParticleType.SAMPLE, 3)
            log.debug("RESULT 2: %s", result2)
            result.extend(result2)
            log.debug("RESULT: %s", result)
            self.assert_data_values(result, 'test_data_3-4.txt.result.yml')
            self.assert_sample_queue_size(DataParticleType.CONTROL, 0)
            self.assert_sample_queue_size(DataParticleType.SAMPLE, 0)
        except SampleTimeout as e:
            log.error("Exception trapped: %s", e, exc_info=True)
            self.fail("Sample timeout.")

