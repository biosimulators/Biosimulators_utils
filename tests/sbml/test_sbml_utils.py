from biosimulators_utils.sbml.utils import get_parameters_variables_for_simulation
from biosimulators_utils.sedml.data_model import (ModelLanguage, SteadyStateSimulation,
                                                  OneStepSimulation, UniformTimeCourseSimulation, Symbol)
from unittest import mock
import libsbml
import os
import unittest


class GetVariableForSimulationTestCase(unittest.TestCase):
    CORE_FIXTURE = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'BIOMD0000000297.xml')
    CORE_FIXTURE_L3 = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'BIOMD0000000075.xml')
    CORE_FIXTURE_WITH_EXTRAS_PARAMS_VARS = os.path.join(
        os.path.dirname(__file__), '..', 'fixtures', 'BIOMD0000000297-params-vars.xml')
    FBC_FIXTURE = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'sbml-fbc-textbook.xml')
    QUAL_FIXTURE = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'Chaouiya-BMC-Syst-Biol-2013-EGF-TNFa-signaling.xml')
    QUAL_FIXTURE_WITH_EXTRAS_PARAMS_VARS = os.path.join(
        os.path.dirname(__file__), '..', 'fixtures', 'Chaouiya-BMC-Syst-Biol-2013-EGF-TNFa-signaling-params-vars.xml')

    def test_core_steady_state(self):
        params, vars = get_parameters_variables_for_simulation(
            self.CORE_FIXTURE, ModelLanguage.SBML, SteadyStateSimulation, 'KISAO_0000019',
            include_compartment_sizes_in_simulation_variables=True,
            include_model_parameters_in_simulation_variables=True)

        self.assertEqual(params[0].id, 'initial_concentration_Trim')
        self.assertEqual(params[0].name, 'initial concentration of CDC28_Clb2_Sic1_Complex')
        self.assertEqual(params[0].new_value, '0.084410675')
        self.assertEqual(params[0].target, "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Trim']/@initialConcentration")
        self.assertEqual(params[0].target_namespaces, {'sbml': 'http://www.sbml.org/sbml/level2/version4'})

        self.assertEqual(params[-3].id, 'mu')
        self.assertEqual(params[-3].new_value, '0.005')

        self.assertEqual(params[-1].id, 'Swe1T')
        self.assertEqual(params[-1].name, None)
        self.assertEqual(params[-1].new_value, '0.0')
        self.assertEqual(params[-1].target, "/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='Swe1T']/@value")
        self.assertEqual(params[-1].target_namespaces, {'sbml': 'http://www.sbml.org/sbml/level2/version4'})

        param = next(param for param in params if param.id == 'initial_size_compartment')
        self.assertEqual(param.name, 'initial size of compartment')
        self.assertEqual(param.new_value, '1.0')
        self.assertEqual(param.target, "/sbml:sbml/sbml:model/sbml:listOfCompartments/sbml:compartment[@id='compartment']/@size")
        self.assertEqual(param.target_namespaces, {'sbml': 'http://www.sbml.org/sbml/level2/version4'})

        self.assertNotEqual(vars[0].id, 'time')

        variable = next((variable for variable in vars if variable.id == 'mass'), None)
        self.assertEqual(variable.id, 'mass')
        self.assertEqual(variable.name, 'mass')
        self.assertEqual(variable.symbol, None)
        self.assertEqual(variable.target, "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='mass']")
        self.assertEqual(variable.target_namespaces, {'sbml': 'http://www.sbml.org/sbml/level2/version4'})

        variable = next((variable for variable in vars if variable.id == 'compartment'), None)
        self.assertEqual(variable, None)

        variable = next(variable for variable in vars if variable.id == 'kswe_dynamics')
        self.assertEqual(variable.name, 'dynamics of kswe')
        self.assertEqual(variable.target, "/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='kswe']/@value")
        self.assertEqual(variable.target_namespaces, {'sbml': 'http://www.sbml.org/sbml/level2/version4'})

        variable = next((variable for variable in vars if variable.id == 'kswe_prime'), None)
        self.assertEqual(variable, None)

    def test_core_steady_state_with_more_params_and_vars(self):
        params, vars = get_parameters_variables_for_simulation(
            self.CORE_FIXTURE_WITH_EXTRAS_PARAMS_VARS, ModelLanguage.SBML, SteadyStateSimulation, 'KISAO_0000019',
            include_compartment_sizes_in_simulation_variables=True,
            include_model_parameters_in_simulation_variables=True)

        self.assertEqual(params[0].id, 'initial_amount_Trim')
        self.assertEqual(params[0].name, 'initial amount of CDC28_Clb2_Sic1_Complex')
        self.assertEqual(params[0].new_value, '0.084410675')
        self.assertEqual(params[0].target, "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species[@id='Trim']/@initialAmount")
        self.assertEqual(params[0].target_namespaces, {'sbml': 'http://www.sbml.org/sbml/level2/version4'})

        param = next(param for param in params if param.id == 'initial_size_compartment')
        self.assertEqual(param.name, 'initial size of compartment')
        self.assertEqual(param.new_value, '1.0')
        self.assertEqual(param.target, "/sbml:sbml/sbml:model/sbml:listOfCompartments/sbml:compartment[@id='compartment']/@size")
        self.assertEqual(param.target_namespaces, {'sbml': 'http://www.sbml.org/sbml/level2/version4'})

        param = next(param for param in params if param.id == 'local_param')
        self.assertEqual(param.name, None)
        self.assertEqual(param.new_value, '10.0')
        self.assertEqual(param.target, ("/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R1']/sbml:kineticLaw"
                                        "/sbml:listOfParameters/sbml:parameter[@id='local_param']/@value"))
        self.assertEqual(param.target_namespaces, {'sbml': 'http://www.sbml.org/sbml/level2/version4'})

        variable = next(variable for variable in vars if variable.id == 'compartment')
        self.assertEqual(variable.name, None)
        self.assertEqual(variable.symbol, None)
        self.assertEqual(variable.target, "/sbml:sbml/sbml:model/sbml:listOfCompartments/sbml:compartment[@id='compartment']/@size")
        self.assertEqual(variable.target_namespaces, {'sbml': 'http://www.sbml.org/sbml/level2/version4'})

        variable = next(variable for variable in vars if variable.id == 'local_param_dynamics')
        self.assertEqual(variable.name, 'dynamics of local_param')
        self.assertEqual(variable.symbol, None)
        self.assertEqual(variable.target, ("/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='R1']/sbml:kineticLaw"
                                           "/sbml:listOfParameters/sbml:parameter[@id='local_param']/@value"))
        self.assertEqual(variable.target_namespaces, {'sbml': 'http://www.sbml.org/sbml/level2/version4'})

        params, vars = get_parameters_variables_for_simulation(
            self.CORE_FIXTURE_WITH_EXTRAS_PARAMS_VARS, ModelLanguage.SBML, SteadyStateSimulation, 'KISAO_0000019',
            include_compartment_sizes_in_simulation_variables=False,
            include_model_parameters_in_simulation_variables=False)
        self.assertNotEqual(next((param for param in params if param.id == 'initial_size_compartment'), None), None)
        self.assertEqual(next((variable for variable in vars if variable.id == 'compartment'), None), None)
        self.assertEqual(next((variable for variable in vars if variable.id == 'local_param_dynamics'), None), None)

    def test_core_one_step(self):
        params, vars = get_parameters_variables_for_simulation(self.CORE_FIXTURE, ModelLanguage.SBML, OneStepSimulation, 'KISAO_0000019')

    def test_core_time_course(self):
        params, vars = get_parameters_variables_for_simulation(
            self.CORE_FIXTURE, ModelLanguage.SBML, UniformTimeCourseSimulation, 'KISAO_0000019')

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

    def test_core_time_course_l3(self):
        params, vars = get_parameters_variables_for_simulation(
            self.CORE_FIXTURE_L3, ModelLanguage.SBML, UniformTimeCourseSimulation, 'KISAO_0000019')

        param = next(param for param in params if param.id == 'k_PIP2hyd')
        self.assertEqual(param.name, 'k_PIP2hyd')
        self.assertEqual(param.new_value, '2.4')
        self.assertEqual(param.target, ("/sbml:sbml/sbml:model/sbml:listOfReactions/sbml:reaction[@id='PIP2_hyd']/sbml:kineticLaw"
                                        "/sbml:listOfLocalParameters/sbml:localParameter[@id='k_PIP2hyd']/@value"))
        self.assertEqual(param.target_namespaces, {'sbml': 'http://www.sbml.org/sbml/level3/version1/core'})

    def test_fbc_steady_state_fba(self):
        params, vars = get_parameters_variables_for_simulation(self.FBC_FIXTURE, ModelLanguage.SBML, SteadyStateSimulation, 'KISAO_0000437')

        self.assertEqual(params[0].id, 'cobra_default_lb')
        self.assertEqual(params[0].name, None)
        self.assertEqual(params[0].target, "/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='cobra_default_lb']/@value")
        self.assertEqual(params[0].target_namespaces, {
            'sbml': 'http://www.sbml.org/sbml/level3/version1/core',
        })
        self.assertEqual(params[0].new_value, '-1000.0')

        self.assertEqual(params[-1].id, 'R_EX_glc__D_e_lower_bound')
        self.assertEqual(params[-1].name, None)
        self.assertEqual(params[-1].target,
                         "/sbml:sbml/sbml:model/sbml:listOfParameters/sbml:parameter[@id='R_EX_glc__D_e_lower_bound']/@value")
        self.assertEqual(params[-1].target_namespaces, {
            'sbml': 'http://www.sbml.org/sbml/level3/version1/core',
        })
        self.assertEqual(params[-1].new_value, '-10.0')

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
        params, vars = get_parameters_variables_for_simulation(self.FBC_FIXTURE, ModelLanguage.SBML, SteadyStateSimulation, 'KISAO_0000526')

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
            get_parameters_variables_for_simulation(self.FBC_FIXTURE, ModelLanguage.SBML, OneStepSimulation, None)

    def test_fbc_time_course(self):
        with self.assertRaises(NotImplementedError):
            get_parameters_variables_for_simulation(self.FBC_FIXTURE, ModelLanguage.SBML, UniformTimeCourseSimulation, None)

    def test_qual_steady_state(self):
        params, vars = get_parameters_variables_for_simulation(
            self.QUAL_FIXTURE, ModelLanguage.SBML, SteadyStateSimulation, 'KISAO_0000450')

        self.assertEqual(vars[0].id, 'erk')
        self.assertEqual(vars[0].name, None)
        self.assertEqual(vars[0].symbol, None)
        self.assertEqual(vars[0].target, "/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@qual:id='erk']")
        self.assertEqual(vars[0].target_namespaces, {
            'sbml': 'http://www.sbml.org/sbml/level3/version1/core',
            'qual': 'http://www.sbml.org/sbml/level3/version1/qual/version1',
        })

    def test_qual_steady_state_with_extra_vars(self):
        params, vars = get_parameters_variables_for_simulation(
            self.QUAL_FIXTURE_WITH_EXTRAS_PARAMS_VARS, ModelLanguage.SBML, SteadyStateSimulation, 'KISAO_0000450',
            include_compartment_sizes_in_simulation_variables=True,
            include_model_parameters_in_simulation_variables=True)

        param = next((param for param in params if param.id == 'initial_level_erk'), None)
        self.assertEqual(param.name, 'initial level of erk')
        self.assertEqual(param.target,
                         "/sbml:sbml/sbml:model/qual:listOfQualitativeSpecies/qual:qualitativeSpecies[@qual:id='erk']/@qual:initialLevel")
        self.assertEqual(param.target_namespaces, {
            'sbml': 'http://www.sbml.org/sbml/level3/version1/core',
            'qual': 'http://www.sbml.org/sbml/level3/version1/qual/version1',
        })
        self.assertEqual(param.new_value, "1")

        param = next((param for param in params if param.id == 'initial_size_main'), None)
        self.assertEqual(param.name, 'initial size of main')
        self.assertEqual(param.target,
                         "/sbml:sbml/sbml:model/sbml:listOfCompartments/sbml:compartment[@id='main']/@size")
        self.assertEqual(param.target_namespaces, {
            'sbml': 'http://www.sbml.org/sbml/level3/version1/core',
        })
        self.assertEqual(param.new_value, "2.5")

        variable = next((variable for variable in vars if variable.id == 'main'), None)
        self.assertEqual(variable.name, None)
        self.assertEqual(variable.target,
                         "/sbml:sbml/sbml:model/sbml:listOfCompartments/sbml:compartment[@id='main']/@size")
        self.assertEqual(variable.target_namespaces, {
            'sbml': 'http://www.sbml.org/sbml/level3/version1/core',
        })

        params, vars = get_parameters_variables_for_simulation(
            self.QUAL_FIXTURE_WITH_EXTRAS_PARAMS_VARS, ModelLanguage.SBML, SteadyStateSimulation, 'KISAO_0000450',
            include_compartment_sizes_in_simulation_variables=False,
            include_model_parameters_in_simulation_variables=False)

        self.assertNotEqual(next((param for param in params if param.id == 'initial_level_erk'), None), None)
        self.assertNotEqual(next((param for param in params if param.id == 'initial_size_main'), None), None)
        self.assertEqual(next((variable for variable in vars if variable.id == 'main'), None), None)

    def test_qual_one_step(self):
        params, vars = get_parameters_variables_for_simulation(self.QUAL_FIXTURE, ModelLanguage.SBML, OneStepSimulation, 'KISAO_0000450')

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
        params, vars = get_parameters_variables_for_simulation(
            self.QUAL_FIXTURE, ModelLanguage.SBML, UniformTimeCourseSimulation, 'KISAO_0000450')

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
            get_parameters_variables_for_simulation('DOES-NOT-EXIST', ModelLanguage.SBML, UniformTimeCourseSimulation, None)

        with self.assertRaises(ValueError):
            get_parameters_variables_for_simulation(__file__, ModelLanguage.SBML, UniformTimeCourseSimulation, None)

        with mock.patch.object(libsbml.Model, 'getNumPlugins', return_value=1):
            with mock.patch.object(libsbml.Model, 'getPlugin', return_value=mock.Mock(getPackageName=lambda: 'other')):
                with self.assertRaises(NotImplementedError):
                    get_parameters_variables_for_simulation(self.CORE_FIXTURE, ModelLanguage.SBML, UniformTimeCourseSimulation, None)

        with self.assertRaises(NotImplementedError):
            get_parameters_variables_for_simulation(self.FBC_FIXTURE, ModelLanguage.SBML, None, None)

        with self.assertRaises(NotImplementedError):
            get_parameters_variables_for_simulation(self.FBC_FIXTURE, ModelLanguage.SBML, SteadyStateSimulation, 'KISAO_0000019')
