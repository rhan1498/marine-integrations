"""
@package mi.dataset.driver.parad_j.cspp.test.test_driver
@file marine-integrations/mi/dataset/driver/parad_j/cspp/driver.py
@author Joe Padula
@brief Test cases for parad_j_cspp driver

USAGE:
 Make tests verbose and provide stdout
   * From the IDK
       $ bin/dsa/test_driver
       $ bin/dsa/test_driver -i [-t testname]
       $ bin/dsa/test_driver -q [-t testname]
"""

__author__ = 'Joe Padula'
__license__ = 'Apache 2.0'

import hashlib
import os

from nose.plugins.attrib import attr

from mi.core.log import get_logger
log = get_logger()

from mi.idk.exceptions import SampleTimeout

from mi.idk.dataset.unit_test import DataSetTestCase
from mi.idk.dataset.unit_test import DataSetIntegrationTestCase
from mi.idk.dataset.unit_test import DataSetQualificationTestCase

from mi.dataset.dataset_driver import \
    DataSourceConfigKey, \
    DataSetDriverConfigKeys

from mi.dataset.driver.parad_j.cspp.driver import \
    ParadJCsppDataSetDriver, \
    DataTypeKey

from mi.dataset.parser.cspp_base import StateKey
from mi.dataset.parser.parad_j_cspp import \
    ParadJCsppMetadataTelemeteredDataParticle, \
    ParadJCsppMetadataRecoveredDataParticle, \
    ParadJCsppInstrumentTelemeteredDataParticle, \
    ParadJCsppInstrumentRecoveredDataParticle

DIR_PARAD_TELEMETERED = '/tmp/parad/telem/test'
DIR_PARAD_RECOVERED = '/tmp/parad/recov/test'

PARAD_REC_PATTERN = '*PPB_PARS.txt'
PARAD_TEL_PATTERN = '*PPD_PARS.txt'

# Driver details
DataSetTestCase.initialize(
    driver_module='mi.dataset.driver.parad_j.cspp.driver',
    driver_class='ParadJCsppDataSetDriver',
    agent_resource_id='123xyz',
    agent_name='Agent007',
    agent_packet_config=ParadJCsppDataSetDriver.stream_config(),
    startup_config={
        DataSourceConfigKey.RESOURCE_ID: 'parad_j_cspp',
        DataSourceConfigKey.HARVESTER:
        {
            DataTypeKey.PARAD_J_CSPP_TELEMETERED: {
                DataSetDriverConfigKeys.DIRECTORY: DIR_PARAD_TELEMETERED,
                DataSetDriverConfigKeys.PATTERN: PARAD_TEL_PATTERN,
                DataSetDriverConfigKeys.FREQUENCY: 1,
            },
            DataTypeKey.PARAD_J_CSPP_RECOVERED: {
                DataSetDriverConfigKeys.DIRECTORY: DIR_PARAD_RECOVERED,
                DataSetDriverConfigKeys.PATTERN: PARAD_REC_PATTERN,
                DataSetDriverConfigKeys.FREQUENCY: 1,
            }
        },
        DataSourceConfigKey.PARSER: {
            DataTypeKey.PARAD_J_CSPP_TELEMETERED: {},
            DataTypeKey.PARAD_J_CSPP_RECOVERED: {}
        }
    }
)

SAMPLE_STREAM = 'parad_j_cspp_parsed'

REC_PARTICLES = (ParadJCsppMetadataRecoveredDataParticle,
                 ParadJCsppInstrumentRecoveredDataParticle)
TEL_PARTICLES = (ParadJCsppMetadataTelemeteredDataParticle,
                 ParadJCsppInstrumentTelemeteredDataParticle)


# The integration and qualification tests generated here are suggested tests,
# but may not be enough to fully test your driver. Additional tests should be
# written as needed.

###############################################################################
#                            INTEGRATION TESTS                                #
# Device specific integration tests are for                                   #
# testing device specific capabilities                                        #
###############################################################################
@attr('INT', group='mi')
class IntegrationTest(DataSetIntegrationTestCase):

    def get_file_state(self, path, ingested=False, position=None, metadata_extracted=False):
        """
        Create a state object for a file. If a position is passed then add a parser state as well.
        """
        mod_time = os.path.getmtime(path)
        file_size = os.path.getsize(path)
        with open(path) as filehandle:
            md5_checksum = hashlib.md5(filehandle.read()).hexdigest()

        parser_state = {
            StateKey.POSITION: position,
            StateKey.METADATA_EXTRACTED: metadata_extracted
        }

        return {
            'ingested': ingested,
            'file_mod_date': mod_time,
            'file_checksum': md5_checksum,
            'file_size': file_size,
            'parser_state': parser_state
        }

    def test_get(self):
        """
        Test that we can get data from files.  Verify that the driver
        sampling can be started and stopped
        """
        log.info("================ START INTEG TEST GET =====================")

        # Start sampling.
        self.driver.start_sampling()
        self.clear_async_data()

        # test that everything works for the telemetered harvester
        self.create_sample_data_set_dir('11079364_PPD_PARS.txt', DIR_PARAD_TELEMETERED)

        log.debug('### Sample file created in dir = %s ', DIR_PARAD_TELEMETERED)

        # check the metadata particle and the first 19 instrument particles
        self.assert_data(TEL_PARTICLES,
                         '11079364_PPD_PARS_telem.yml',
                         count=20, timeout=10)

        # test that everything works for the recovered harvester
        self.create_sample_data_set_dir('11079364_PPB_PARS.txt', DIR_PARAD_RECOVERED)

        log.debug('### Sample file created in dir = %s ', DIR_PARAD_RECOVERED)

        # check the metadata particle and the first 19 instrument particles
        self.assert_data(REC_PARTICLES,
                         '11079364_PPB_PARS_recov.yml',
                         count=20, timeout=10)

    def test_mid_state_start(self):
        """
        Test the ability to start the driver with a saved state
        """
        log.info("================ START INTEG TEST MID STATE START =====================")

        recovered_file_one = '11079364_PPB_PARS.txt'
        telemetered_file_one = '11079364_PPD_PARS.txt'

        # Clear any existing sampling
        self.clear_sample_data()

        recovered_path_1 = self.create_sample_data_set_dir(recovered_file_one, DIR_PARAD_RECOVERED)
        telemetered_path_1 = self.create_sample_data_set_dir(telemetered_file_one, DIR_PARAD_TELEMETERED)

        # For recovered, we will assume first 19 records have bee processed and put position to 20
        # For telemetered, we will assume first 13 records have been processed and put position to 14
        state = {
            DataTypeKey.PARAD_J_CSPP_RECOVERED: {
                recovered_file_one: self.get_file_state(recovered_path_1,
                                                        ingested=False,
                                                        position=1114,
                                                        metadata_extracted=True),
            },
            DataTypeKey.PARAD_J_CSPP_TELEMETERED: {
                telemetered_file_one: self.get_file_state(telemetered_path_1,
                                                          ingested=False,
                                                          position=829,
                                                          metadata_extracted=True),
            }
        }

        driver = self._get_driver_object(memento=state)

        # create some data to parse
        self.clear_async_data()

        driver.start_sampling()

        # verify data is produced
        self.assert_data(REC_PARTICLES, 'test_recovered_midstate_start.yml', count=1, timeout=10)

        self.assert_data(TEL_PARTICLES, 'test_telemetered_midstate_start.yml', count=2, timeout=10)

    def test_start_stop_resume(self):
        """
        Test the ability to stop and restart sampling, ingesting files in the
        correct order
        """
        recovered_file_one = '11079364_PPB_PARS.txt'
        telemetered_file_one = '11079364_PPD_PARS.txt'

        # Clear any existing sampling
        self.clear_sample_data()

        self.create_sample_data_set_dir(recovered_file_one, DIR_PARAD_RECOVERED)
        self.create_sample_data_set_dir(telemetered_file_one, DIR_PARAD_TELEMETERED)

        # create some data to parse
        self.clear_async_data()

        self.driver.start_sampling()

        # verify data is produced
        self.assert_data(REC_PARTICLES, 'test_recovered_start_stop_resume_one.yml', count=1, timeout=10)

        self.assert_data(TEL_PARTICLES, 'test_telemetered_start_stop_resume_one.yml', count=1, timeout=10)

        self.driver.stop_sampling()

        self.driver.start_sampling()

        # verify data is produced
        self.assert_data(REC_PARTICLES, 'test_recovered_start_stop_resume_two.yml', count=4, timeout=10)

        self.assert_data(TEL_PARTICLES, 'test_telemetered_start_stop_resume_two.yml', count=4, timeout=10)

        self.driver.stop_sampling()

    def test_sample_exception(self):
        """
        Test a case that should produce a sample exception and confirm the
        sample exception occurs
        """
        log.info("================ START INTEG TEST SAMPLE EXCEPTION =====================")

        # Start sampling.
        self.driver.start_sampling()
        self.clear_async_data()

        # test that everything works for the telemetered harvester
        self.create_sample_data_set_dir('11079364_BAD_PPB_PARS.txt', DIR_PARAD_RECOVERED)

        # an event catches the sample exception
        self.assert_event('ResourceAgentErrorEvent')

    def test_harvester_new_file_exception(self):
        """
        Test an exception raised after the driver is started during
        the file read.  Should call the exception callback.
        """

        # create the file so that it is unreadable
        self.create_sample_data_set_dir("11079364_PPD_PARS.txt", DIR_PARAD_TELEMETERED,
                                        mode=000)

        # Start sampling and watch for an exception
        self.driver.start_sampling()

        self.assert_exception(IOError)

        # At this point the harvester thread is dead.  The agent
        # exception handle should handle this case.

    def test_harvester_new_file_exception_recovered(self):
        """
        Test an exception raised after the driver is started during
        the file read.  Should call the exception callback.
        """

        # create the file so that it is unreadable
        self.create_sample_data_set_dir("11079364_PPB_PARS.txt", DIR_PARAD_RECOVERED,
                                        mode=000)

        # Start sampling and watch for an exception
        self.driver.start_sampling()

        self.assert_exception(IOError)

        # At this point the harvester thread is dead.  The agent
        # exception handle should handle this case.


###############################################################################
#                            QUALIFICATION TESTS                              #
# Device specific qualification tests are for                                 #
# testing device specific capabilities                                        #
###############################################################################
@attr('QUAL', group='mi')
class QualificationTest(DataSetQualificationTestCase):

    def test_publish_path(self):
        """
        Setup an agent/driver/harvester/parser and verify that data is
        published out the agent
        """
        pass

    def test_large_import(self):
        """
        Test importing a large number of samples from the file at once
        """
        pass

    def test_stop_start(self):
        """
        Test the agents ability to start data flowing, stop, then restart
        at the correct spot.
        """
        pass

    def test_shutdown_restart(self):
        """
        Test a full stop of the dataset agent, then restart the agent 
        and confirm it restarts at the correct spot.
        """
        pass

    def test_parser_exception(self):
        """
        Test an exception is raised after the driver is started during
        record parsing.
        """
        pass

