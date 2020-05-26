import webapp2
import textwrap
import inspect

from google.appengine.ext import ndb

NO_VAR = 'No variable named '
NO_COMMANDS = 'NO COMMANDS'
CLEANED = 'CLEANED'
IS_NONE = ' = None'
NO_VARIABLE_ERROR = 'Error: Please enter variable name/value'


class Variable(ndb.Model):
    name = ndb.StringProperty()
    values = ndb.StringProperty(repeated=True)
    index = ndb.IntegerProperty()

    @staticmethod
    def get_var(name): 
        var_key = ndb.Key('Variable', name)
        v = Variable.query(ancestor=var_key).fetch(1)

        if len(v):
            return v[0]
        else:
            return None

    @staticmethod
    def set_var(var, value): 
        var.index += 1
        var.values.insert(var.index, value)
        var.put();
   
    @staticmethod
    def get_enteties(): 
        return Variable.query().fetch()

    @staticmethod
    def create(name, value):
        variable = Variable(key=ndb.Key('Variable', name))
        variable.name = name
        variable.values = [value]
        variable.index = 0
        variable.put()

class Operations(ndb.Model):
    list = ndb.StringProperty(repeated=True)
    index = ndb.IntegerProperty()

    @staticmethod
    def add(varName):
        op = Operations.get()
        op.index += 1
        op.list.insert(op.index, varName)
        op.put()

    @staticmethod
    def create():
        variable = Operations(key=ndb.Key('Operations', 'operations'))
        variable.list = []
        variable.index = -1
        variable.put()

    @staticmethod
    def get(): 
        var_key = ndb.Key('Operations', 'operations')
        v = Operations.query(ancestor=var_key).fetch(1)

        if len(v):
            return v[0]
        else:
            return None
 
def getParams(self, key):
    return str(self.GET.get(key))

def responseHandler(self, text):
    self.response.headers.add_header('Access-Control-Allow-Origin', '*')
    self.response.out.write(text)

def SetHandler(self):
    name = getParams(self, 'name')
    value = getParams(self, 'value')

    if not name or not value:
        return responseHandler(self, NO_VARIABLE_ERROR)

    variable = Variable.get_var(name)

    if variable:
        Variable.set_var(variable, value)
    else:
        Variable.create(name, value)

    Operations.add(name)

    return responseHandler(self, name + " = " + value)

def GetHandler(self):
    name = getParams(self, 'name')
    variable = Variable.get_var(name)

    if variable:
        if variable.index == -1:
            return responseHandler(self, 'None')
        return responseHandler(self, variable.values[variable.index])
   
    responseHandler(self, NO_VAR + name)

def UnsetHandler(self):
    name = getParams(self, 'name')

    if not name:
        return responseHandler(self, NO_VAR + name)

    variable = Variable.get_var(name)

    if not variable:
        return responseHandler(self, NO_VAR + name)

    Variable.set_var(variable, 'None')

    Operations.add(name)

    return responseHandler(self, name + IS_NONE )

def NumEqualToHandler(self):
    value = getParams(self, 'value')

    if not value:
        return responseHandler(self, NO_VARIABLE_ERROR)


    variables = Variable.get_enteties()

    count = 0

    for var in variables:
        if value == var.values[var.index]:
            count+=1

    return responseHandler(self, count)

def UndoHandler(self):
    ops = Operations.get();

    if ops.index == -1:
        return responseHandler(self, NO_COMMANDS)

    varName = ops.list[ops.index]
    variable = Variable.get_var(varName)

    ops.index -= 1
    variable.index -= 1

    variable.put();
    ops.put();

    if variable.index == -1:
        return responseHandler(self, varName + IS_NONE)

    return responseHandler(self, varName + ' = ' + variable.values[variable.index])

def RedoHandler(self):
    ops = Operations.get();

    if ops.index == len(ops.list) - 1:
        return responseHandler(self, NO_COMMANDS)

    ops.index += 1
    varName = ops.list[ops.index]
    variable = Variable.get_var(varName)

    variable.index += 1

    variable.put();
    ops.put();

    if variable.index == -1:
        return responseHandler(self, varName + IS_NONE)

    return responseHandler(self, varName + ' = ' + variable.values[variable.index])

def EndHandler(self):
    variables = Variable.get_enteties()

    # variables
    for var in variables:
        var.key.delete()

    # operations
    ops = Operations.get()
    ops.key.delete()

    # get ready to the next wave
    init()

    return responseHandler(self, CLEANED)

def init():
    Operations.create()

def main():
    init()

    return webapp2.WSGIApplication([
        ('/get',    GetHandler),
        ('/set',    SetHandler),
        ('/unset', UnsetHandler),
        ('/numequalto', NumEqualToHandler),
        ('/undo',    UndoHandler),
        ('/redo',    RedoHandler),
        ('/end',    EndHandler)     
   ], debug=False)

application = main()
