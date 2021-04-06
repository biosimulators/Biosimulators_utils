from biosimulators_utils.sbml.utils import get_variables_for_simulation
from biosimulators_utils.sedml.data_model import (ModelLanguage, SteadyStateSimulation,
                                                  OneStepSimulation, UniformTimeCourseSimulation, Symbol)
from unittest import mock
import libsbml
import os
import unittest


class GetVariableForSimulationTestCase(unittest.TestCase):
    CORE_FIXTURE = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'BIOMD0000000297.xml')
    FBC_FIXTURE = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sbml-fbc-textbook.xml')
    QUAL_FIXTURE = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'Chaouiya-BMC-Syst-Biol-2013-EGF-TNFa-signaling.xml')

    def test_core_steady_state(self):
        vars = get_variables_for_simulation(self.CORE_FIXTURE, ModelLanguage.SBML, SteadyStateSimulation, 'KISAO_0000019')

        self.assertNotEqual(vars[0].id, 'time')

        self.assertEqual(vars[-1].id, 'mass')
        self.assertEqual(vars[-1].name, 'mass')
        self.assertEqual(vars[-1].symbol, None)
        self.assertEqual(vars[-1].target, "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='mass']")
        self.assertEqual(vars[-1].target_namespaces, {'sbml': 'http://www.sbml.org/sbml/level2/version4'})

    def test_core_one_step(self):
        vars = get_variables_for_simulation(self.CORE_FIXTURE, ModelLanguage.SBML, OneStepSimulation, 'KISAO_0000019')

    def test_core_time_course(self):
        vars = get_variables_for_simulation(self.CORE_FIXTURE, ModelLanguage.SBML, UniformTimeCourseSimulation, 'KISAO_0000019')

        self.assertEqual(vars[0].id, 'time')
        self.assertEqual(vars[0].name, 'Time')
        self.assertEqual(vars[0].symbol, Symbol.time)
        self.assertEqual(vars[0].target, None)
        self.assertEqual(vars[0].target_namespaces, {})

        self.assertEqual(vars[-1].id, 'mass')
        self.assertEqual(vars[-1].name, 'mass')
        self.assertEqual(vars[-1].symbol, None)
        self.assertEqual(vars[-1].target, "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='mass']")
        self.assertEqual(vars[-1].target_namespaces, {'sbml': 'http://www.sbml.org/sbml/level2/version4'})

    def test_fbc_steady_state_fba(self):
        vars = get_variables_for_simulation(self.FBC_FIXTURE, ModelLanguage.SBML, SteadyStateSimulation, 'KISAO_0000437')

        self.assertEqual(vars[0].id, 'obj')
        self.assertEqual(vars[0].name, None)
        self.assertEqual(vars[0].symbol, None)
        self.assertEqual(vars[0].target, "/sbml:sbml/sbml:model/fbc:listOfObjectives/fbc:objective[@fbc:id='obj']/@value")
        self.assertEqual(vars[0].target_namespaces, {
            'sbml': 'http://www.sbml.org/sbml/level3/version1/core',
            'fbc': 'http://www.sbml.org/sbml/level3/version1/fbc/version2',
        })

        self.assertEqual(vars[-1].id, 'R_TPI')
        self.assertEqual(vars[-1].name, 'triose-phosphate isomerase')
        self.assertEqual(vars[-1].symbol, None)
        self.assertEqual(vars[-1].target, "/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_TPI']/@flux")
        self.assertEqual(vars[-1].target_namespaces, {'sbml': 'http://www.sbml.org/sbml/level3/version1/core'})

    def test_fbc_steady_state_fva(self):
        vars = get_variables_for_simulation(self.FBC_FIXTURE, ModelLanguage.SBML, SteadyStateSimulation, 'KISAO_0000526')

        self.assertEqual(vars[0].id, 'R_ACALD_min')
        self.assertEqual(vars[0].name, 'acetaldehyde dehydrogenase (acetylating) min')
        self.assertEqual(vars[0].symbol, None)
        self.assertEqual(vars[0].target, "/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_ACALD']/@minFlux")
        self.assertEqual(vars[0].target_namespaces, {'sbml': 'http://www.sbml.org/sbml/level3/version1/core'})

        self.assertEqual(vars[-1].id, 'R_TPI_max')
        self.assertEqual(vars[-1].name, 'triose-phosphate isomerase max')
        self.assertEqual(vars[-1].symbol, None)
        self.assertEqual(vars[-1].target, "/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R_TPI']/@maxFlux")
        self.assertEqual(vars[-1].target_namespaces, {'sbml': 'http://www.sbml.org/sbml/level3/version1/core'})

    def test_fbc_one_step(self):
        with self.assertRaises(NotImplementedError):
            get_variables_for_simulation(self.FBC_FIXTURE, ModelLanguage.SBML, OneStepSimulation, None)

    def test_fbc_time_course(self):
        with self.assertRaises(NotImplementedError):
            get_variables_for_simulation(self.FBC_FIXTURE, ModelLanguage.SBML, UniformTimeCourseSimulation, None)

    def test_qual_steady_state(self):
        vars = get_variables_for_simulation(self.QUAL_FIXTURE, ModelLanguage.SBML, SteadyStateSimulation, 'KISAO_0000450')

        self.assertEqual(vars[0].id, 'erk')
        self.assertEqual(vars[0].name, None)
        self.assertEqual(vars[0].symbol, None)
        self.assertEqual(vars[0].target, "/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@qual:id='erk']")
        self.assertEqual(vars[0].target_namespaces, {
            'sbml': 'http://www.sbml.org/sbml/level3/version1/core',
            'qual': 'http://www.sbml.org/sbml/level3/version1/qual/version1',
        })

    def test_qual_one_step(self):
        vars = get_variables_for_simulation(self.QUAL_FIXTURE, ModelLanguage.SBML, OneStepSimulation, 'KISAO_0000450')

        self.assertEqual(vars[0].id, 'time')
        self.assertEqual(vars[0].name, 'Time')
        self.assertEqual(vars[0].symbol, Symbol.time)
        self.assertEqual(vars[0].target, None)
        self.assertEqual(vars[0].target_namespaces, {})

        self.assertEqual(vars[-1].id, 'nik')
        self.assertEqual(vars[-1].name, None)
        self.assertEqual(vars[-1].symbol, None)
        self.assertEqual(vars[-1].target, "/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@qual:id='nik']")
        self.assertEqual(vars[-1].target_namespaces, {
            'sbml': 'http://www.sbml.org/sbml/level3/version1/core',
            'qual': 'http://www.sbml.org/sbml/level3/version1/qual/version1',
        })

    def test_qual_time_course(self):
        vars = get_variables_for_simulation(self.QUAL_FIXTURE, ModelLanguage.SBML, UniformTimeCourseSimulation, 'KISAO_0000450')

        self.assertEqual(vars[0].id, 'time')
        self.assertEqual(vars[0].name, 'Time')
        self.assertEqual(vars[0].symbol, Symbol.time)
        self.assertEqual(vars[0].target, None)
        self.assertEqual(vars[0].target_namespaces, {})

        self.assertEqual(vars[-1].id, 'nik')
        self.assertEqual(vars[-1].name, None)
        self.assertEqual(vars[-1].symbol, None)
        self.assertEqual(vars[-1].target, "/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@qual:id='nik']")
        self.assertEqual(vars[-1].target_namespaces, {
            'sbml': 'http://www.sbml.org/sbml/level3/version1/core',
            'qual': 'http://www.sbml.org/sbml/level3/version1/qual/version1',
        })

    def test_error_handling(self):
        with self.assertRaises(FileNotFoundError):
            get_variables_for_simulation('DOES-NOT-EXIST', ModelLanguage.SBML, UniformTimeCourseSimulation, None)

        with self.assertRaises(ValueError):
            get_variables_for_simulation(__file__, ModelLanguage.SBML, UniformTimeCourseSimulation, None)

        with mock.patch.object(libsbml.Model, 'getNumPlugins', return_value=1):
            with mock.patch.object(libsbml.Model, 'getPlugin', return_value=mock.Mock(getPackageName=lambda: 'other')):
                with self.assertRaises(NotImplementedError):
                    get_variables_for_simulation(self.CORE_FIXTURE, ModelLanguage.SBML, UniformTimeCourseSimulation, None)

        with self.assertRaises(NotImplementedError):
            get_variables_for_simulation(self.FBC_FIXTURE, ModelLanguage.SBML, None, None)

        with self.assertRaises(NotImplementedError):
            get_variables_for_simulation(self.FBC_FIXTURE, ModelLanguage.SBML, SteadyStateSimulation, 'KISAO_0000019')
