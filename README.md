# Identity trace Python Agent

This library is used for executing functions and tests inside python applications with or without the [Identity Server](https://github.com/identity-reporting/identity-server).

### Installation
This library can be installed inside your python app using
```
pip install identity-trace-python-agent
```

### Configuration
In the root of your python project, it is required to create a file `identity_config.json`. This file is used to configure how `identity-trace-python-agent` and Identity Server runs tests and functions inside your python app.

`identity_config.json`

```
{
	"modules": { // Tracer will decorate all the functions inside the modules listed in the modules
		"your_python_module": true // This will decorate all the functions and classes inside the module
		"another_module": [... String list of function and class names to decorate]
	},
	"python_path": "/Users/mamoon/.local/share/virtualenvs/your-env-name/bin/python", // path to your virtual env python executable. You can set it to "python3" or "python" if you want to use the global python without virtual env.
	"server_port": 8002, // Port on which Identity server will start. You can then visit http://localhost:8002 To access the identity server web app.
	"max_executed_functions": 100 // Number of executed function records to keep. 0 means unlimited. Limiting it will be good for storage space.
	"tests_directory": "tests" // directory where Identity Server will create tests. Defaults to "tests". 
}
```

### Run Tests In CI/CD Pipeline
Unit tests can be executed in your CI/CD pipeline using the following command.
```
python -m identity_trace --runTests
```

### Filter Tests
You can provider different filter arguments to execute unit tests based on those filters.

###### Filter By Test Suite Name
Filter by test suite name. This command will run all the tests where test suite name contains `some_test`.
```
python -m identity_trace --runTests --name="some_test"
```
###### Filter By Module Name
Filter by module name. This command will run all the tests where module name contains `some_module_name`.
```
python -m identity_trace --runTests --moduleName="some_module_name"
```
###### Filter By File Name
Filter by file name. This command will run all the tests where file name contains `some_file`.
```
python -m identity_trace --runTests --fileName="some_file"
```
