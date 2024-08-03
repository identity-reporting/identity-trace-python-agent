from typing import Any, Dict, List, Optional, Union

class TestRunForTestSuite:
    def __init__(self, name, description, functionMeta, testSuiteID, tests):
        self.name = name
        self.description = description
        self.functionMeta = functionMeta
        self.testSuiteID = testSuiteID
        self.tests = tests

class TestResult:
    def __init__(self, testCaseName, testCaseDescription, functionMeta, testSuiteID, successful, result):
        self.testCaseName = testCaseName
        self.testCaseDescription = testCaseDescription
        self.functionMeta = functionMeta
        self.testSuiteID = testSuiteID
        self.successful = successful
        self.result = result
    
    def serialize(self):

        return dict(
            testCaseName = self.testCaseName,
            testCaseDescription = self.testCaseDescription,
            functionMeta = self.functionMeta,
            testSuiteID = self.testSuiteID,
            successful = self.successful,
            result = [ 
                dict(
                    expectation = r["expectation"],
                    result = r["result"].serialize() if r["result"] else None,
                    successful = r["successful"],
                    error = r["error"]
                ) for r in self.result
            ]
        )


class FunctionTestResult:
    def __init__(self, _type, assertions, children, executedSuccessfully, executionContext, id, failureReasons, name, ignored, successful, thrownError, passedInput):
        self._type = _type
        self.assertions = assertions
        self.children = children
        self.executedSuccessfully = executedSuccessfully
        self.executionContext = executionContext
        self.id = id
        self.failureReasons = failureReasons
        self.name = name
        self.ignored = ignored
        self.successful = successful
        self.thrownError = thrownError
        self.passedInput = passedInput
    
    def serialize(self):

        return dict(
            _type = self._type,
            children = [r.serialize() for r in self.children],
            executedSuccessfully = self.executedSuccessfully,
            executionContext = self.executionContext,
            id = self.id,
            failureReasons = self.failureReasons,
            assertions = self.assertions,
            name = self.name,
            ignored = self.ignored,
            successful = self.successful,
            thrownError = self.thrownError,
            passedInput = self.passedInput
        )

def matchExecutionWithTestConfig(testRun: TestRunForTestSuite) -> TestResult:
    
    results = []
    for i, t in enumerate(testRun.tests):
        if t.get("error", None):
            results.append(dict(
                expectation = testRun.tests[i]['name'],
                result = None,
                successful = False,
                error = t["error"]
            ))
        else:
            res = matchFunctionWithConfig(t.get('executedFunction', None), t['config'])
            results.append(dict(
                expectation = testRun.tests[i]['name'],
                result = res,
                successful = res.successful,
                error = None
            ))
        

    return TestResult(
        testCaseName=testRun.name,
        testCaseDescription=testRun.description,
        functionMeta=testRun.functionMeta,
        testSuiteID=testRun.testSuiteID,
        successful=all(r["successful"] for r in results),
        result=results
    )

def matchFunctionWithConfig(executedFunction: Optional[Dict[str, Any]], config: Dict[str, Any]) -> FunctionTestResult:
    successful = True
    
    if not executedFunction:
        return FunctionTestResult(
            _type="FunctionTestResult",
            assertions=[],
            children=[],
            executedSuccessfully=False,
            executionContext={},
            id=config['functionMeta']['id'],
            failureReasons=["Did not get called."],
            name=config['functionMeta']['name'],
            ignored=False,
            successful=False,
            thrownError="",
            passedInput=None
        )
    
    assertionResults = []
    for assertion in config['assertions']:
        failureReasons = []
        assertionResult = {}

        if 'expectedErrorMessage' in assertion:
            thrownError = executedFunction.get('error')
            conf = assertion['expectedErrorMessage']
            if conf['operator'] == "equals" and thrownError != conf['message']:
                failureReasons.append("Error message does not match.")
            elif conf['operator'] == "contains" and (thrownError is None or conf['message'] not in thrownError):
                failureReasons.append(f'Error message does not contain "{conf["message"]}"')

            assertionResult['expectedErrorMessage'] = {
                'message': assertion['expectedErrorMessage']['message'],
                'operator': assertion['expectedErrorMessage']['operator'],
                'receivedError': thrownError,
            }
        elif 'ioConfig' in assertion:
            def matchObject(label, operator, sourceObject, targetObject):
                if operator == "equals" and not objectIsEqual(sourceObject, targetObject):
                    failureReasons.append(f"{label} does not match the expectation.")
                elif operator == "contains" and not objectContains(sourceObject, targetObject):
                    failureReasons.append(f"{label} does not match the expectation.")

            if assertion['ioConfig']['target'] == "input":
                matchObject("Input", assertion['ioConfig']['operator'], assertion['ioConfig']['object'], executedFunction['input'])
            else:
                matchObject("Output", assertion['ioConfig']['operator'], assertion['ioConfig']['object'], executedFunction['output'])

            assertionResult['ioConfig'] = {
                'target': assertion['ioConfig']['target'],
                'object': assertion['ioConfig']['object'],
                'operator': assertion['ioConfig']['operator'],
                'receivedObject': executedFunction['output'] if assertion['ioConfig']['target'] == "output" else executedFunction['input'],
            }

        assertionResult['name'] = assertion['name']
        assertionResult['success'] = len(failureReasons) == 0
        assertionResult['failureReasons'] = failureReasons
        if not assertionResult['success']:
            successful = False
        assertionResults.append(assertionResult)

    failureReasons = []
    childrenResults = []
    for i, f in enumerate(config['children']):
        child_function_at_index = None
        try:
            child_function_at_index = executedFunction['children'][i]
        except:
            child_function_at_index = None

        childResult = matchFunctionWithConfig(child_function_at_index if 'children' in executedFunction else None, f)
        if not isResultSuccessful(childResult):
            successful = False
            failureReasons.append(f"Child function {f['functionMeta']['name']}.")
        childrenResults.append(childResult)

    return FunctionTestResult(
        _type="FunctionTestResult",
        failureReasons=failureReasons,
        successful=successful,
        ignored=False,
        name=config['functionMeta']['name'],
        children=childrenResults,
        executedSuccessfully=executedFunction['executedSuccessfully'],
        thrownError=executedFunction['error'],
        executionContext=executedFunction['executionContext'],
        id=executedFunction['id'],
        assertions=assertionResults,
        passedInput=executedFunction.get("input", None)
    )

def isResultSuccessful(obj: FunctionTestResult) -> bool:
    return obj.ignored or obj.successful

def objectIsEqual(src: Any, target: Any) -> bool:
    if isinstance(src, list):
        if not isinstance(target, list):
            return False
        return all(objectIsEqual(item, target[i]) for i, item in enumerate(src))
    elif isinstance(src, dict):
        if not isinstance(target, dict):
            return False
        return all(objectIsEqual(src[k], target.get(k)) for k in src)
    else:
        return src == target

def objectContains(src: Any, target: Any) -> bool:
    if isinstance(src, list):
        if not isinstance(target, list):
            return False
        return all(objectIsEqual(item, target[i]) for i, item in enumerate(src))
    elif isinstance(src, dict):
        return all(objectIsEqual(src[k], target.get(k)) for k in src)
    else:
        return src == target
