
import inspect
from unittest.mock import patch
from unittest import mock
import uuid
from .utils import TestCase


from identity_trace.tracer import general_postprocessing_tracer, general_preprocessing_tracer
from identity_trace.wrappers import ClientExecutedFunctionTrace





class general_preprocessing_tracer_tests(TestCase):

    def test_copies_input(self):
        '''
            Tests whether the tracer copies function input if configured to do so in the 
            function specific config.
        '''
        
        trace = ClientExecutedFunctionTrace()
        frame = inspect.currentframe()
        function_input = []

        input_serializer = mock.Mock()
        input_serializer.return_value = uuid.uuid4()
        config = dict(
            copy_input = True,
            input_serializer = input_serializer,
            find_parent = False
        )

        general_preprocessing_tracer(
            config,
            trace,
            frame,
            function_input
        )

        input_serializer.assert_called_once_with(function_input)
        self.assertEqual(
            trace.execution_context["copy_input"], True
        )
        self.assertEqual(
            trace.input, input_serializer.return_value
        )
    

    def test_sets_input_serializer_error_in_context(self):
        '''
            Sets input serializer error in the context
        '''
        
        trace = ClientExecutedFunctionTrace()
        frame = inspect.currentframe()
        function_input = []

        input_serializer = mock.Mock()
        input_serializer.side_effect = Exception("an error") 
        config = dict(
            copy_input = True,
            input_serializer = input_serializer,
            find_parent = False
        )

        general_preprocessing_tracer(
            config,
            trace,
            frame,
            function_input
        )

        input_serializer.assert_called_once_with(function_input)
        self.assertEqual(
            trace.execution_context["copy_input"], True
        )
        self.assertEqual(
            trace.input, None
        )
        self.assertEqual(
            trace.execution_context["copy_input_error"], "an error"
        )

        
    


    @patch("identity_trace.tracer.register_function")
    @patch("identity_trace.tracer.register_frame")
    def test_registers_frame(self, register_frame_mock, register_function_mock):
        '''
            If find_parent is configured to true. Then it should register the frame
            and function by id. So that this function can be found when its children
            are called.
        '''
        
        config = dict(
            copy_input = False,
            input_serializer = lambda x: x,
            find_parent = True
        )

        trace = ClientExecutedFunctionTrace()
        frame = inspect.currentframe()
        function_input = []

        general_preprocessing_tracer(
            config,
            trace,
            frame,
            function_input
        )

        register_frame_mock.assert_called_once_with(
            str(id(frame)), trace
        )
        register_function_mock.assert_called_once_with(
            trace.id,
            trace
        )

        # since this is a root function
        # there should be no parent id
        self.assertEqual(trace.parent_id, None)
    

    @patch("identity_trace.tracer.is_frame_registered")
    @patch("identity_trace.tracer.register_function")
    @patch("identity_trace.tracer.register_frame")
    def test_finds_parent(self, register_frame_mock, register_function_mock, is_frame_registered_mock):
        '''
            Finds the parent if there is a frame registered previously.
        '''
        
        config = dict(
            copy_input = False,
            input_serializer = lambda x: x,
            find_parent = True
        )

        trace = ClientExecutedFunctionTrace()
        parent_trace = ClientExecutedFunctionTrace()
        frame = inspect.currentframe()
        function_input = []

        is_frame_registered_mock.return_value = parent_trace

        general_preprocessing_tracer(
            config,
            trace,
            frame,
            function_input
        )

        self.assertEqual(trace.parent_id, parent_trace.id)
        is_frame_registered_mock.assert_called_once_with(str(id(frame.f_back)))



class general_postprocessing_tracer_tests(TestCase):


    def test_copies_output(self):
        '''
            Tests whether the tracer copies function output if configured to do so in the 
            function specific config.
        '''
        
        trace = ClientExecutedFunctionTrace()
        frame = inspect.currentframe()
        function_output = uuid.uuid4()

        output_serializer = mock.Mock()
        output_serializer.return_value = uuid.uuid4()
        config = dict(
            copy_output = True,
            output_serializer = output_serializer,
            find_parent = False
        )

        general_postprocessing_tracer(
            config,
            trace,
            frame,
            function_output
        )

        output_serializer.assert_called_once_with(function_output)
        self.assertEqual(
            trace.execution_context["copy_output"], True
        )

        self.assertEqual(
            trace.output, output_serializer.return_value
        )
    

    def test_copies_output_in_context(self):
        '''
            Tests whether the tracer copies function output serializer error in the execution
            context
        '''
        
        trace = ClientExecutedFunctionTrace()
        frame = inspect.currentframe()
        function_output = uuid.uuid4()

        output_serializer = mock.Mock()
        output_serializer.side_effect = Exception("an error")

        config = dict(
            copy_output = True,
            output_serializer = output_serializer,
            find_parent = False
        )

        general_postprocessing_tracer(
            config,
            trace,
            frame,
            function_output
        )

        output_serializer.assert_called_once_with(function_output)
        self.assertEqual(
            trace.execution_context["copy_output"], True
        )

        self.assertEqual(
            trace.output, None
        )
        self.assertEqual(
            trace.execution_context["copy_output_error"], "an error"
        )
    
    @patch("identity_trace.tracer.remove_frame")
    @patch("identity_trace.tracer.remove_function")
    def test_removes_frame_and_function(self, remove_function_mock, remove_frame_mock):
        '''
            Tracer should remove frame and function since there wont be any function needing it.
        '''
        
        trace = ClientExecutedFunctionTrace()
        frame = inspect.currentframe()
        function_output = uuid.uuid4()

        output_serializer = mock.Mock()

        config = dict(
            copy_output = False,
            output_serializer = output_serializer,
            find_parent = True
        )

        general_postprocessing_tracer(
            config,
            trace,
            frame,
            function_output
        )

        remove_frame_mock.assert_called_once_with(
            str(id(frame))
        )
        remove_function_mock.assert_called_once_with(trace.id)
    

    @patch("identity_trace.tracer.get_function_by_name")
    def test_adds_children_to_parent(self, get_function_by_name_mock):
        '''
            Tracer should append the child to parent function if it has parent id
        '''
        
        trace = ClientExecutedFunctionTrace()
        parent_trace = ClientExecutedFunctionTrace()

        

        frame = inspect.currentframe()
        function_output = uuid.uuid4()
        get_function_by_name_mock.return_value = parent_trace

        output_serializer = mock.Mock()

        config = dict(
            copy_output = False,
            output_serializer = output_serializer,
            find_parent = False
        )

        general_postprocessing_tracer(
            config,
            trace,
            frame,
            function_output
        )

        self.assertEqual(
            parent_trace.children, [], "Should be empty children if no children"
        )

        # set the parent id manually
        trace.parent_id = parent_trace.id

        general_postprocessing_tracer(
            config,
            trace,
            frame,
            function_output
        )

        self.assertEqual(
            parent_trace.children, [trace], "Tracer should trace to parent trace children"
        )
    
    @patch("identity_trace.tracer.get_function_by_name")
    def test_invalid_parent_id(self, get_function_by_name_mock):
        '''
            Tracer should throw error if parent function id is not registered.
        '''
        
        trace = ClientExecutedFunctionTrace()
        parent_trace = ClientExecutedFunctionTrace()

        

        frame = inspect.currentframe()
        function_output = uuid.uuid4()
        get_function_by_name_mock.return_value = None

        output_serializer = mock.Mock()

        config = dict(
            copy_output = False,
            output_serializer = output_serializer,
            find_parent = False
        )

        # set the parent id manually
        trace.parent_id = "invalid_id"
        trace.name = "some_func"

        with self.assertRaises(Exception) as exception:

            general_postprocessing_tracer(
                config,
                trace,
                frame,
                function_output
            )

        self.assert_exception_matches(
            Exception((
                f"Parent ID ({trace.parent_id}) is set on "
                f"client executed function ({trace.name}) but "
                f"parent function ID ({trace.parent_id}) is not registered."
            )),
            exception.exception
        )

