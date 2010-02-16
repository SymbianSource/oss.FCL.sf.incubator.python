
/* Use this file as a template to start implementing a module that
   also declares object types. All occurrences of 'Xxo' should be changed
   to something reasonable for your objects. After that, all other
   occurrences of 'xx' should be changed to something reasonable for your
   module. If your module is named foo your sourcefile should be named
   foomodule.c.

   You will probably want to delete all references to 'x_attr' and add
   your own types of attributes instead.  Maybe you want to name your
   local variables other than 'self'.  If your object type is needed in
   other files, you'll have to create a file "foobarobject.h"; see
   intobject.h for an example. */

/* DistutilsDemo objects */

#include "Python.h"

static PyObject *ErrorObject;

typedef struct {
	PyObject_HEAD
	PyObject	*x_attr;	/* Attributes dictionary */
} DistutilsDemoObject;

static PyTypeObject DistutilsDemo_Type;

#define DistutilsDemoObject_Check(v)	((v)->ob_type == &DistutilsDemo_Type)

static DistutilsDemoObject *
newDistutilsDemoObject(PyObject *arg)
{
	DistutilsDemoObject *self;
	self = PyObject_New(DistutilsDemoObject, &DistutilsDemo_Type);
	if (self == NULL)
		return NULL;
	self->x_attr = NULL;
	return self;
}

/* DistutilsDemo methods */

static void
DistutilsDemo_dealloc(DistutilsDemoObject *self)
{
	Py_XDECREF(self->x_attr);
	PyObject_Del(self);
}

static PyObject *
DistutilsDemo_demo(DistutilsDemoObject *self, PyObject *args)
{
	if (!PyArg_ParseTuple(args, ":demo"))
		return NULL;
	Py_INCREF(Py_None);
	return Py_None;
}

static PyMethodDef DistutilsDemo_methods[] = {
	{"demo",	(PyCFunction)DistutilsDemo_demo,	METH_VARARGS,
		PyDoc_STR("demo() -> None")},
	{NULL,		NULL}		/* sentinel */
};

static PyObject *
DistutilsDemo_getattr(DistutilsDemoObject *self, char *name)
{
	if (self->x_attr != NULL) {
		PyObject *v = PyDict_GetItemString(self->x_attr, name);
		if (v != NULL) {
			Py_INCREF(v);
			return v;
		}
	}
	return Py_FindMethod(DistutilsDemo_methods, (PyObject *)self, name);
}

static int
DistutilsDemo_setattr(DistutilsDemoObject *self, char *name, PyObject *v)
{
	if (self->x_attr == NULL) {
		self->x_attr = PyDict_New();
		if (self->x_attr == NULL)
			return -1;
	}
	if (v == NULL) {
		int rv = PyDict_DelItemString(self->x_attr, name);
		if (rv < 0)
			PyErr_SetString(PyExc_AttributeError,
			        "delete non-existing DistutilsDemo attribute");
		return rv;
	}
	else
		return PyDict_SetItemString(self->x_attr, name, v);
}

static PyTypeObject DistutilsDemo_Type = {
	/* The ob_type field must be initialized in the module init function
	 * to be portable to Windows without using C++. */
	PyObject_HEAD_INIT(NULL)
	0,			/*ob_size*/
	"distutils_demo2.DistutilsDemo",		/*tp_name*/
	sizeof(DistutilsDemoObject),	/*tp_basicsize*/
	0,			/*tp_itemsize*/
	/* methods */
	(destructor)DistutilsDemo_dealloc, /*tp_dealloc*/
	0,			/*tp_print*/
	(getattrfunc)DistutilsDemo_getattr, /*tp_getattr*/
	(setattrfunc)DistutilsDemo_setattr, /*tp_setattr*/
	0,			/*tp_compare*/
	0,			/*tp_repr*/
	0,			/*tp_as_number*/
	0,			/*tp_as_sequence*/
	0,			/*tp_as_mapping*/
	0,			/*tp_hash*/
        0,                      /*tp_call*/
        0,                      /*tp_str*/
        0,                      /*tp_getattro*/
        0,                      /*tp_setattro*/
        0,                      /*tp_as_buffer*/
        Py_TPFLAGS_DEFAULT,     /*tp_flags*/
        0,                      /*tp_doc*/
        0,                      /*tp_traverse*/
        0,                      /*tp_clear*/
        0,                      /*tp_richcompare*/
        0,                      /*tp_weaklistoffset*/
        0,                      /*tp_iter*/
        0,                      /*tp_iternext*/
        0,                      /*tp_methods*/
        0,                      /*tp_members*/
        0,                      /*tp_getset*/
        0,                      /*tp_base*/
        0,                      /*tp_dict*/
        0,                      /*tp_descr_get*/
        0,                      /*tp_descr_set*/
        0,                      /*tp_dictoffset*/
        0,                      /*tp_init*/
        0,                      /*tp_alloc*/
        0,                      /*tp_new*/
        0,                      /*tp_free*/
        0,                      /*tp_is_gc*/
};
/* --------------------------------------------------------------------- */

/* Function of two integers returning integer */

PyDoc_STRVAR(distutils_demo2_foo_doc,
"foo(i,j)\n\
\n\
Return the sum of i and j.");

static PyObject *
distutils_demo2_foo(PyObject *self, PyObject *args)
{
	long i, j;
	long res;
	if (!PyArg_ParseTuple(args, "ll:foo", &i, &j))
		return NULL;
	res = i+j; /* XXX Do something here */
	return PyInt_FromLong(res);
}


/* Function of no arguments returning new DistutilsDemo object */

static PyObject *
distutils_demo2_new(PyObject *self, PyObject *args)
{
	DistutilsDemoObject *rv;

	if (!PyArg_ParseTuple(args, ":new"))
		return NULL;
	rv = newDistutilsDemoObject(args);
	if (rv == NULL)
		return NULL;
	return (PyObject *)rv;
}

/* Example with subtle bug from extensions manual ("Thin Ice"). */

static PyObject *
distutils_demo2_bug(PyObject *self, PyObject *args)
{
	PyObject *list, *item;

	if (!PyArg_ParseTuple(args, "O:bug", &list))
		return NULL;

	item = PyList_GetItem(list, 0);
	/* Py_INCREF(item); */
	PyList_SetItem(list, 1, PyInt_FromLong(0L));
	PyObject_Print(item, stdout, 0);
	printf("\n");
	/* Py_DECREF(item); */

	Py_INCREF(Py_None);
	return Py_None;
}

/* Test bad format character */

static PyObject *
distutils_demo2_roj(PyObject *self, PyObject *args)
{
	PyObject *a;
	long b;
	if (!PyArg_ParseTuple(args, "O#:roj", &a, &b))
		return NULL;
	Py_INCREF(Py_None);
	return Py_None;
}


/* ---------- */

static PyTypeObject Str_Type = {
	/* The ob_type field must be initialized in the module init function
	 * to be portable to Windows without using C++. */
	PyObject_HEAD_INIT(NULL)
	0,			/*ob_size*/
	"distutils_demo2_module.Str",		/*tp_name*/
	0,			/*tp_basicsize*/
	0,			/*tp_itemsize*/
	/* methods */
	0,			/*tp_dealloc*/
	0,			/*tp_print*/
	0,			/*tp_getattr*/
	0,			/*tp_setattr*/
	0,			/*tp_compare*/
	0,			/*tp_repr*/
	0,			/*tp_as_number*/
	0,			/*tp_as_sequence*/
	0,			/*tp_as_mapping*/
	0,			/*tp_hash*/
	0,			/*tp_call*/
	0,			/*tp_str*/
	0,			/*tp_getattro*/
	0,			/*tp_setattro*/
	0,			/*tp_as_buffer*/
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
	0,			/*tp_doc*/
	0,			/*tp_traverse*/
	0,			/*tp_clear*/
	0,			/*tp_richcompare*/
	0,			/*tp_weaklistoffset*/
	0,			/*tp_iter*/
	0,			/*tp_iternext*/
	0,			/*tp_methods*/
	0,			/*tp_members*/
	0,			/*tp_getset*/
	&PyString_Type,		/*tp_base*/
	0,			/*tp_dict*/
	0,			/*tp_descr_get*/
	0,			/*tp_descr_set*/
	0,			/*tp_dictoffset*/
	0,			/*tp_init*/
	0,			/*tp_alloc*/
	0,			/*tp_new*/
	0,			/*tp_free*/
	0,			/*tp_is_gc*/
};

/* ---------- */

static PyObject *
null_richcompare(PyObject *self, PyObject *other, int op)
{
	Py_INCREF(Py_NotImplemented);
	return Py_NotImplemented;
}

static PyTypeObject Null_Type = {
	/* The ob_type field must be initialized in the module init function
	 * to be portable to Windows without using C++. */
	PyObject_HEAD_INIT(NULL)
	0,			/*ob_size*/
	"distutils_demo2_module.Null",	/*tp_name*/
	0,			/*tp_basicsize*/
	0,			/*tp_itemsize*/
	/* methods */
	0,			/*tp_dealloc*/
	0,			/*tp_print*/
	0,			/*tp_getattr*/
	0,			/*tp_setattr*/
	0,			/*tp_compare*/
	0,			/*tp_repr*/
	0,			/*tp_as_number*/
	0,			/*tp_as_sequence*/
	0,			/*tp_as_mapping*/
	0,			/*tp_hash*/
	0,			/*tp_call*/
	0,			/*tp_str*/
	0,			/*tp_getattro*/
	0,			/*tp_setattro*/
	0,			/*tp_as_buffer*/
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
	0,			/*tp_doc*/
	0,			/*tp_traverse*/
	0,			/*tp_clear*/
	null_richcompare,	/*tp_richcompare*/
	0,			/*tp_weaklistoffset*/
	0,			/*tp_iter*/
	0,			/*tp_iternext*/
	0,			/*tp_methods*/
	0,			/*tp_members*/
	0,			/*tp_getset*/
	&PyBaseObject_Type,	/*tp_base*/
	0,			/*tp_dict*/
	0,			/*tp_descr_get*/
	0,			/*tp_descr_set*/
	0,			/*tp_dictoffset*/
	0,			/*tp_init*/
	0,			/*tp_alloc*/
	PyType_GenericNew,	/*tp_new*/
	0,			/*tp_free*/
	0,			/*tp_is_gc*/
};


/* ---------- */


/* List of functions defined in the module */

static PyMethodDef distutils_demo2_methods[] = {
	{"roj",		distutils_demo2_roj,		METH_VARARGS,
		PyDoc_STR("roj(a,b) -> None")},
	{"foo",		distutils_demo2_foo,		METH_VARARGS,
	 	distutils_demo2_foo_doc},
	{"new",		distutils_demo2_new,		METH_VARARGS,
		PyDoc_STR("new() -> new Xx object")},
	{"bug",		distutils_demo2_bug,		METH_VARARGS,
		PyDoc_STR("bug(o) -> None")},
	{NULL,		NULL}		/* sentinel */
};

PyDoc_STRVAR(module_doc,
"This is a template module just for instruction.");

/* Initialization function for the module (*must* be called initdistutils_demo2) */

PyMODINIT_FUNC
initdistutils_demo2(void)
{
	PyObject *m;

	/* Finalize the type object including setting type of the new type
	 * object; doing it here is required for portability to Windows 
	 * without requiring C++. */
	if (PyType_Ready(&DistutilsDemo_Type) < 0)
		return;

	/* Create the module and add the functions */
	m = Py_InitModule3("distutils_demo2", distutils_demo2_methods, module_doc);
	if (m == NULL)
		return;

	/* Add some symbolic constants to the module */
	if (ErrorObject == NULL) {
		ErrorObject = PyErr_NewException("distutils_demo2.error", NULL, NULL);
		if (ErrorObject == NULL)
			return;
	}
	Py_INCREF(ErrorObject);
	PyModule_AddObject(m, "error", ErrorObject);

	/* Add Str */
	if (PyType_Ready(&Str_Type) < 0)
		return;
	PyModule_AddObject(m, "Str", (PyObject *)&Str_Type);

	/* Add Null */
	if (PyType_Ready(&Null_Type) < 0)
		return;
	PyModule_AddObject(m, "Null", (PyObject *)&Null_Type);
}
