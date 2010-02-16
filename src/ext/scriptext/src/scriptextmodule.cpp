/* Copyright (c) 2008 - 2009 Nokia Corporation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include "scriptextmodule.h"
#include <datetime.h>

using namespace LIW;
#define SEARCH_KEY_LEN  30

static PyObject *liw_error = NULL;
static PyObject *indexerr = NULL;

static TBool lock_enable_securitymanager = EFalse;
static TBool enable_securitymanager = EFalse;

/* Forward declarations */
struct SPyLiwMapWrapper;
struct SPyLiwListWrapper;
PyObject* SPyValue_FromVariant(TLiwVariant &);
static Py_ssize_t SPyLiwMapWrapper_len(SPyLiwMapWrapper *);
static PyObject *SPyLiwListWrapper_item(SPyLiwListWrapper *, Py_ssize_t);
static TLiwVariant SPyVariant_FromValue(PyObject *);
static bool SPyVariant_FromValue(PyObject *, TLiwVariant &);

PyObject*
SPyLiwErr_SetString(char *err_string, int err_no=0)
{
    if (!err_no)
        PyErr_SetString(liw_error, err_string);
    else {
        PyObject *v = Py_BuildValue("(is)", err_no, err_string);
        PyErr_SetObject(liw_error, v);
    }

    return NULL;
}

/********* Python LIWIterable wrapper Object *******************/

struct SPyLiwIterableWrapper {
    PyObject_HEAD
    CLiwIterable *iter;
};

struct SPyLiwIterableIter {
    PyObject_HEAD
    SPyLiwIterableWrapper *ii_iter;
};

static void
SPyLiwIterableWrapper_dealloc(SPyLiwIterableWrapper *liw_iter)
{
    liw_iter->iter->DecRef();
    PyObject_Del(liw_iter);
}

static void
SPyLiwIterableIter_dealloc(SPyLiwIterableIter *ii)
{
    Py_DECREF(ii->ii_iter);
    PyObject_Del(ii);
}

static PyMethodDef liwiterable_methods[] = {
    {NULL,    NULL}   /* sentinel */
};

static PyObject *
SPyLiwIterableIter_next(SPyLiwIterableIter *ii)
{
    assert(ii->ii_iter);

    TLiwVariant entry;
    TBool res = EFalse;

    entry.PushL();
    TRAPD(error, res = ii->ii_iter->iter->NextL(entry));
    CleanupStack::Pop(&entry);
    if (error != KErrNone)
        return SPyLiwErr_SetString("error accessing next element", error);

    if (!res)
        return NULL;

    PyObject *ret = SPyValue_FromVariant(entry);
    entry.Reset();

    return ret;
}

PyTypeObject SPyLiwIterableIterType = {
    PyObject_HEAD_INIT(&PyType_Type)
    0,                          /* ob_size */
    "scriptext.scriptextiterableiter",  /* tp_name */
    sizeof(SPyLiwIterableIter), /* tp_basicsize */
    0,                          /* tp_itemsize */
    /* methods */
    (destructor)SPyLiwIterableIter_dealloc,  /* tp_dealloc */
    0,                          /* tp_print */
    0,                          /* tp_getattr */
    0,                          /* tp_setattr */
    0,                          /* tp_compare */
    0,                          /* tp_repr */
    0,                          /* tp_as_number */
    0,                          /* tp_as_sequence */
    0,                          /* tp_as_mapping */
    0,                          /* tp_hash */
    0,                          /* tp_call */
    0,                          /* tp_str */
    PyObject_GenericGetAttr,    /* tp_getattro */
    0,                          /* tp_setattro */
    0,                          /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,/* tp_flags */
    0,                          /* tp_doc */
    0,                          /* tp_traverse */
    0,                          /* tp_clear */
    0,                          /* tp_richcompare */
    0,                          /* tp_weaklistoffset */
    PyObject_SelfIter,          /* tp_iter */
    (iternextfunc)SPyLiwIterableIter_next,/* tp_iternext */
    0,                          /* tp_methods */
    0                           /* tp_members */
};

static PyObject *
SPyLiwIterableIter_new(SPyLiwIterableWrapper *liw_iter, PyTypeObject *itertype)
{
    SPyLiwIterableIter *ii;
    ii = PyObject_New(SPyLiwIterableIter, itertype);
    if (ii == NULL)
        return NULL;

    Py_INCREF(liw_iter);
    ii->ii_iter = liw_iter;

    return (PyObject *)ii;
}

static PyObject *
SPyLiwIterableIter_iter(SPyLiwIterableWrapper *liw_iter)
{
    return SPyLiwIterableIter_new(liw_iter, &SPyLiwIterableIterType);
}

extern "C"
PyTypeObject SPyLiwIterableWrapperType = {
    PyObject_HEAD_INIT(NULL)
    0,                              /* ob_size */
    "scriptext.scriptextiterable",  /* tp_name */
    sizeof(SPyLiwIterableWrapper),  /* tp_basicsize */
    0,                              /* tp_itemsize */
    (destructor)SPyLiwIterableWrapper_dealloc, /* tp_dealloc */
    0,                         /* tp_print */
    0,                         /* tp_getattr */
    0,                         /* tp_setattr */
    0,                         /* tp_compare */
    0,                         /* tp_repr */
    0,                         /* tp_as_number */
    0,                         /* tp_as_sequence */
    0,                         /* tp_as_mapping */
    0,                         /* tp_hash */
    0,                         /* tp_call */
    0,                         /* tp_str */
    0,                         /* tp_getattro */
    0,                         /* tp_setattro */
    0,                         /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,        /* tp_flags */
    "ScriptextIterable objects",     /* tp_doc */
    0,                         /* tp_traverse */
    0,                         /* tp_clear */
    0,                         /* tp_richcompare */
    0,                         /* tp_weaklistoffset */
    (getiterfunc)SPyLiwIterableIter_iter, /* tp_iter */
    0,                         /* tp_iternext */
    liwiterable_methods,       /* tp_methods */
    0,                         /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    0,                         /* tp_init */
    PyType_GenericAlloc,       /* tp_alloc */
    0,                         /* tp_new */
};

extern "C" SPyLiwIterableWrapper *
SPyLiwIterableWrapper_FromLiwIterable(CLiwIterable *iterable)
{
    SPyLiwIterableWrapper *py_wrapper = (SPyLiwIterableWrapper *)
                     PyType_GenericNew(&SPyLiwIterableWrapperType, NULL, NULL);

    if (!py_wrapper)
        return NULL;

    py_wrapper->iter = iterable;
    py_wrapper->iter->IncRef();
    return py_wrapper;
}

/********* Python LIWList wrapper Object *******************/

struct SPyLiwListWrapper {
    PyObject_HEAD
    const CLiwList *list;
};

struct SPyLiwListIterator {
    PyObject_HEAD
    SPyLiwListWrapper *li_list;
    int current_index;
};

static void
SPyLiwListIterator_dealloc(SPyLiwListIterator *li)
{
    Py_DECREF(li->li_list);
    PyObject_Del(li);
}

static PyObject *
SPyLiwListIterator_next(SPyLiwListIterator *li)
{
    assert(li->li_list);

    TInt index = li->current_index;

    PyObject *ret_val = NULL;
    ret_val = SPyLiwListWrapper_item(li->li_list, index);

    if (ret_val)
        li->current_index += 1;

    return ret_val;
}

static PyMethodDef SPyLiwListIterator_methods[] = {
         {NULL,     NULL}     /* sentinel */
};

static PyObject *
SPyLiwListIterator_new(SPyLiwListWrapper *liw_list, PyTypeObject *itertype)
{
    SPyLiwListIterator *li;
    li = PyObject_New(SPyLiwListIterator, itertype);
    if (li == NULL)
        return NULL;

    Py_INCREF(liw_list);
    li->li_list = liw_list;
    li->current_index = 0;

    return (PyObject *)li;
}

PyTypeObject SPyLiwListIteratorType = {
    PyObject_HEAD_INIT(&PyType_Type)
    0,                          /* ob_size */
    "scriptext.scriptextlistiterator",  /* tp_name */
    sizeof(SPyLiwListIterator), /* tp_basicsize */
    0,                          /* tp_itemsize */
    /* methods */
    (destructor)SPyLiwListIterator_dealloc,  /* tp_dealloc */
    0,                          /* tp_print */
    0,                          /* tp_getattr */
    0,                          /* tp_setattr */
    0,                          /* tp_compare */
    0,                          /* tp_repr */
    0,                          /* tp_as_number */
    0,                          /* tp_as_sequence */
    0,                          /* tp_as_mapping */
    0,                          /* tp_hash */
    0,                          /* tp_call */
    0,                          /* tp_str */
    PyObject_GenericGetAttr,    /* tp_getattro */
    0,                          /* tp_setattro */
    0,                          /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,/* tp_flags */
    0,                          /* tp_doc */
    0,                          /* tp_traverse */
    0,                          /* tp_clear */
    0,                          /* tp_richcompare */
    0,                          /* tp_weaklistoffset */
    PyObject_SelfIter,          /* tp_iter */
    (iternextfunc)SPyLiwListIterator_next,/* tp_iternext */
    SPyLiwListIterator_methods,           /* tp_methods */
    0                           /* tp_members */
};

static PyObject *
SPyLiwListIterator_iter(SPyLiwListWrapper *liw_list)
{
    return SPyLiwListIterator_new(liw_list, &SPyLiwListIteratorType);
}

static Py_ssize_t
SPyLiwListWrapper_length(SPyLiwListWrapper *liw_list)
{
    return liw_list->list->Count();
}

/* Return item corresponding to the given index */
static PyObject *
SPyLiwListWrapper_item(SPyLiwListWrapper *liw_list, Py_ssize_t i)
{
    TLiwVariant ent;

    assert(liw_list->list);

    if (i < 0 || i >= liw_list->list->Count())
    {
         if (indexerr == NULL)
             indexerr = PyString_FromString( "list index out of range");
         PyErr_SetObject(PyExc_IndexError, indexerr);
         return NULL;
    }

    ent.PushL();
    TRAPD(error, liw_list->list->AtL(i, ent));
    CleanupStack::Pop(&ent);
    if (error != KErrNone)
        return SPyLiwErr_SetString("error accessing element", error);

    PyObject *ret = SPyValue_FromVariant(ent);
    ent.Reset();

    return ret;
}

static PySequenceMethods liwlist_as_sequence = {
    (lenfunc)SPyLiwListWrapper_length, /* sq_length */
    0,                                 /* sq_concat */
    0,                                 /* sq_repeat */
    (ssizeargfunc)SPyLiwListWrapper_item,/* sq_item */
    0,                                 /* sq_slice */
    0,                                 /* sq_ass_item */
    0,                                 /* sq_ass_slice */
    0,                                 /* sq_contains */
    0,                                 /* sq_inplace_concat */
    0,                                 /* sq_inplace_repeat */
};

static PyMethodDef liwlist_methods[] = {
     {NULL,      NULL}   /* sentinel */
};

static void
SPyLiwListWrapper_dealloc(SPyLiwListWrapper *liw_list)
{
    const_cast<CLiwList*> (liw_list->list)->DecRef();
    PyObject_Del(liw_list);
}

extern "C"
PyTypeObject SPyLiwListWrapperType = {
    PyObject_HEAD_INIT(NULL)
    0,                         /* ob_size */
    "scriptext.scriptextlist",  /* tp_name */
    sizeof(SPyLiwListWrapper), /* tp_basicsize */
    0,                         /* tp_itemsize */
    (destructor)SPyLiwListWrapper_dealloc, /* tp_dealloc */
    0,                         /* tp_print */
    0,                         /* tp_getattr */
    0,                         /* tp_setattr */
    0,                         /* tp_compare */
    0,                         /* tp_repr */
    0,                         /* tp_as_number */
    &liwlist_as_sequence,      /* tp_as_sequence */
    0,                         /* tp_as_mapping */
    0,                         /* tp_hash */
    0,                         /* tp_call */
    0,                         /* tp_str */
    0,                         /* tp_getattro */
    0,                         /* tp_setattro */
    0,                         /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,        /* tp_flags */
    "ScriptextList objects",         /* tp_doc */
    0,                         /* tp_traverse */
    0,                         /* tp_clear */
    0,                         /* tp_richcompare */
    0,                         /* tp_weaklistoffset */
    (getiterfunc)SPyLiwListIterator_iter,   /* tp_iter */
    0,                         /* tp_iternext */
    liwlist_methods,           /* tp_methods */
    0,                         /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    0,                         /* tp_init */
    PyType_GenericAlloc,       /* tp_alloc */
    0,                         /* tp_new */
};

extern "C" SPyLiwListWrapper *
SPyLiwListWrapper_FromLiwList(const CLiwList *list)
{
    SPyLiwListWrapper *py_wrapper = (SPyLiwListWrapper *)
                     PyType_GenericNew(&SPyLiwListWrapperType, NULL, NULL);

    if (!py_wrapper)
        return NULL;

    py_wrapper->list = list;
    const_cast<CLiwList*> (py_wrapper->list)->IncRef();
    return py_wrapper;
}

/********* Python LIWMap wrapper Object *******************/

struct SPyLiwMapWrapper {
    PyObject_HEAD
    const CLiwMap *map;
};

struct SPyLiwMapKeyIterator {
    PyObject_HEAD
    SPyLiwMapWrapper *mi_map;
    int current_index;
};

static PyObject *
SPyLiwMapKeyIterator_new(SPyLiwMapWrapper *liw_map, PyTypeObject *itertype)
{
    SPyLiwMapKeyIterator *mi;
    mi = PyObject_New(SPyLiwMapKeyIterator, itertype);
    if (mi == NULL)
        return NULL;

    Py_INCREF(liw_map);
    mi->mi_map = liw_map;
    mi->current_index = 0;

    return (PyObject *)mi;
}

static void
SPyLiwMapKeyIterator_dealloc(SPyLiwMapKeyIterator *mi)
{
    Py_DECREF(mi->mi_map);
    PyObject_Del(mi);
}

static void
set_key_error(PyObject *arg)
{
    PyObject *tup;
    tup = PyTuple_Pack(1, arg);
    if (!tup)
        return; /* caller will expect error to be set anyway */
    PyErr_SetObject(PyExc_KeyError, tup);
    Py_DECREF(tup);
}

static PyObject *
SPyLiwMapKeyIterator_iternextkey(SPyLiwMapKeyIterator *mi)
{
    int i;
    TBuf8<128> key;

    assert(mi->mi_map);

    i = mi->current_index;
    if (i<0 || i >= mi->mi_map->map->Count())
        return NULL;

    TRAPD(error, mi->mi_map->map->AtL(i, key));
    if (error != KErrNone)
        return SPyLiwErr_SetString("error accessing next key", error);

    mi->current_index += 1;
    return Py_BuildValue("s#", key.Ptr(), key.Length());
}

static PyObject *
SPyLiwMapKeyIterator_iter_len(SPyLiwMapKeyIterator *mi)
{
    Py_ssize_t len = SPyLiwMapWrapper_len(mi->mi_map);
    return PyInt_FromSize_t(len);
}

static PyMethodDef liwmapkeyiter_methods[] = {
    {"__length_hint__", (PyCFunction)SPyLiwMapKeyIterator_iter_len,
                        METH_NOARGS, NULL},
    {NULL, NULL}       /* sentinel */
};

PyTypeObject SPyLiwMapKeyIteratorType = {
    PyObject_HEAD_INIT(&PyType_Type)
    0,                                  /* ob_size */
    "scriptext.scriptextmapkeyiterator",  /* tp_name */
    sizeof(SPyLiwMapKeyIterator),       /* tp_basicsize */
    0,                                  /* tp_itemsize */
    /* methods */
    (destructor)SPyLiwMapKeyIterator_dealloc, /* tp_dealloc */
    0,                                  /* tp_print */
    0,                                  /* tp_getattr */
    0,                                  /* tp_setattr */
    0,                                  /* tp_compare */
    0,                                  /* tp_repr */
    0,                                  /* tp_as_number */
    0,                                  /* tp_as_sequence */
    0,                                  /* tp_as_mapping */
    0,                                  /* tp_hash */
    0,                                  /* tp_call */
    0,                                  /* tp_str */
    PyObject_GenericGetAttr,            /* tp_getattro */
    0,                                  /* tp_setattro */
    0,                                  /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,                 /* tp_flags */
    0,                                  /* tp_doc */
    0,                                  /* tp_traverse */
    0,                                  /* tp_clear */
    0,                                  /* tp_richcompare */
    0,                                  /* tp_weaklistoffset */
    PyObject_SelfIter,                  /* tp_iter */
    (iternextfunc)SPyLiwMapKeyIterator_iternextkey,   /* tp_iternext */
    liwmapkeyiter_methods,              /* tp_methods */
    0,
};

static PyObject *
SPyLiwMapKeyIterator_iter(SPyLiwMapWrapper *liw_map)
{
    return SPyLiwMapKeyIterator_new(liw_map, &SPyLiwMapKeyIteratorType);
}

static void
SPyLiwMapWrapper_dealloc(SPyLiwMapWrapper *liw_map)
{
    const_cast<CLiwMap*> (liw_map->map)->DecRef();
    PyObject_Del(liw_map);
}

static Py_ssize_t
SPyLiwMapWrapper_len(SPyLiwMapWrapper *liw_map)
{
    assert(liw_map->map);
    return liw_map->map->Count();
}

/* Return the value corresponding to `key` */
static PyObject *
SPyLiwMapWrapper_subscript(SPyLiwMapWrapper *liw_map, register PyObject *key)
{
    assert(liw_map->map);

    if (!PyString_Check(key))
    {
        PyErr_SetString(PyExc_TypeError, "key should be a string");
        return NULL;
    }

    char *key_ptr = PyString_AS_STRING(key);
    int key_l = PyString_Size(key);
    TPtrC8 key_c((const unsigned char*)key_ptr, key_l);

    TLiwVariant value;
    TBool found = EFalse;

    value.PushL();
    TRAPD(error, found = liw_map->map->FindL(key_c, value));
    CleanupStack::Pop(&value);
    if (error != KErrNone)
        return SPyLiwErr_SetString("error accessing element", error);

    if (!found)
    {
        set_key_error(key);
        return NULL;
    }

    PyObject *ret = SPyValue_FromVariant(value);
    value.Reset();

    return ret;
}

/* Return 1 if `key` is in liwmap `op`, 0 if not, and -1 on error. */
int
SPyLiwMapWrapper_contains(PyObject *op, PyObject *key)
{
    SPyLiwMapWrapper *liw_map = (SPyLiwMapWrapper *)op;
    assert(liw_map->map);

    if (!PyString_Check(key))
    {
        PyErr_SetString(PyExc_TypeError, "key should be a string");
        return -1;
    }

    char *key_ptr = PyString_AS_STRING(key);
    int key_l = PyString_Size(key);
    TPtrC8 key_c((const unsigned char*)key_ptr, key_l);

    TLiwVariant value;
    TBool found = EFalse;

    value.PushL();
    TRAPD(error, found = liw_map->map->FindL(key_c, value));
    CleanupStack::Pop(&value);
    if (error != KErrNone)
    {
        SPyLiwErr_SetString("error accessing element", error);
        return -1;
    }

    value.Reset();

    return found? 1 : 0;
}

static PySequenceMethods liwmap_as_sequence = {
    0,                          /* sq_length */
    0,                          /* sq_concat */
    0,                          /* sq_repeat */
    0,                          /* sq_item */
    0,                          /* sq_slice */
    0,                          /* sq_ass_item */
    0,                          /* sq_ass_slice */
    SPyLiwMapWrapper_contains,  /* sq_contains */
    0,                          /* sq_inplace_concat */
    0,                          /* sq_inplace_repeat */
};

static PyMappingMethods liwmap_as_mapping = {
    (lenfunc)SPyLiwMapWrapper_len,        /*mp_length*/
    (binaryfunc)SPyLiwMapWrapper_subscript,  /*mp_subscript*/
    0, /*mp_ass_subscript*/
};

static PyMethodDef liwmap_methods[] = {
     {NULL,      NULL}   /* sentinel */
};

extern "C"
PyTypeObject SPyLiwMapWrapperType = {
    PyObject_HEAD_INIT(NULL)
    0,                         /* ob_size */
    "scriptext.scriptextmap",  /* tp_name */
    sizeof(SPyLiwMapWrapper),  /* tp_basicsize */
    0,                         /* tp_itemsize */
    (destructor)SPyLiwMapWrapper_dealloc, /* tp_dealloc */
    0,                         /* tp_print */
    0,                         /* tp_getattr */
    0,                         /* tp_setattr */
    0,                         /* tp_compare */
    0,                         /* tp_repr */
    0,                         /* tp_as_number */
    &liwmap_as_sequence,        /*tp_as_sequence*/
    &liwmap_as_mapping,        /* tp_as_mapping */
    0,                         /* tp_hash */
    0,                         /* tp_call */
    0,                         /* tp_str */
    0,                         /* tp_getattro */
    0,                         /* tp_setattro */
    0,                         /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT, /* tp_flags */
    "ScriptextMap objects",   /* tp_doc */
    0,               /* tp_traverse */
    0,               /* tp_clear */
    0,               /* tp_richcompare */
    0,               /* tp_weaklistoffset */
    (getiterfunc)SPyLiwMapKeyIterator_iter, /* tp_iter */
    0,               /* tp_iternext */
    liwmap_methods,  /* tp_methods */
    0,               /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    0,                         /* tp_init */
    PyType_GenericAlloc,       /* tp_alloc */
    0,                 /* tp_new */
};

extern "C" SPyLiwMapWrapper *
SPyLiwMapWrapper_FromLiwMap(const CLiwMap *map)
{
    SPyLiwMapWrapper *py_wrapper = (SPyLiwMapWrapper *)
                     PyType_GenericNew(&SPyLiwMapWrapperType, NULL, NULL);

    if (!py_wrapper)
        return NULL;

    py_wrapper->map = map;
    const_cast<CLiwMap*> (py_wrapper->map)->IncRef();
    return py_wrapper;
}

PyObject *
SPyValue_FromVariant(TLiwVariant &value)
{
    PyObject *py_value = NULL;

    switch (value.TypeId()) {

        case EVariantTypeTBool:
            py_value = Py_BuildValue("i", value.AsTBool());
            break;

        case EVariantTypeTInt32:
            py_value = Py_BuildValue("i", value.AsTInt32());
            break;

        case EVariantTypeTTime:
            py_value = epoch_to_datetime(value.AsTTime());
            if (py_value == NULL)
            {
                PyErr_SetString(PyExc_TypeError,
                                "Retrieving the time failed");
            }
            Py_INCREF(py_value);
            break;

        case EVariantTypeTUint:
            py_value = Py_BuildValue("I", value.AsTUint());
            break;

        case EVariantTypeTReal:
            py_value = Py_BuildValue("f", value.AsTReal());
            break;

        case EVariantTypeTUid:
            py_value = Py_BuildValue("i", value.AsTUid().iUid);
            break;

        case EVariantTypeDesC:
            TPtrC val_c((TUint16*)value.AsDes().Ptr(), value.AsDes().Length());
            TInt len = val_c.Length();
            py_value = Py_BuildValue("u#", val_c.Ptr(), len);
            break;

        case EVariantTypeDesC8:
            TPtrC8 val_c8((TUint8*)value.AsDes().Ptr(), value.AsDes().Length());
            TInt len8 = val_c8.Length();
            py_value = Py_BuildValue("s#", val_c8.Ptr(), len8);
            break;

        case EVariantTypeMap:
            const CLiwMap *map = value.AsMap();
            py_value = (PyObject *)SPyLiwMapWrapper_FromLiwMap(map);
            break;

        case EVariantTypeList:
            const CLiwList *list = value.AsList();
            py_value = (PyObject *)SPyLiwListWrapper_FromLiwList(list);
            break;

        case EVariantTypeIterable:
            CLiwIterable *iter = value.AsIterable();
            py_value = (PyObject *)SPyLiwIterableWrapper_FromLiwIterable(iter);
            break;

        default:
            py_value = SPyLiwErr_SetString("unsupported scriptext variant");
            break;
    }

    return py_value;
}

static bool
SPyLiwMap_FromDict(PyObject *dict, TLiwVariant &liw_variant)
{
    CLiwDefaultMap* pMap = CLiwDefaultMap::NewL();
    CleanupClosePushL(*pMap);
    TInt index = 0;
    PyObject *key = NULL, *value = NULL;
    while (PyDict_Next(dict, &index, &key, &value))
    {
        if (!PyString_Check(key))
        {
            PyErr_SetString(PyExc_TypeError, "key should be a string");
            pMap->DecRef();
            return false;
        }
        const char *key_ptr = PyString_AsString(key);
        int key_l = PyString_Size(key);
        TPtrC8 key_c((const unsigned char*)key_ptr, key_l);

        if (0 >= key_l)
        {
            PyErr_SetString(PyExc_KeyError, "key cannot be a null string");
            pMap->DecRef();
            return false;
        }

        TLiwVariant val_c;
        if(!SPyVariant_FromValue(value, val_c))
        {
            pMap->DecRef();
            return false;
        }
        val_c.PushL();
        TRAPD(err, pMap->InsertL(key_c, val_c));
        CleanupStack::Pop(&val_c);
        if (err != KErrNone)
        {
            SPyLiwErr_SetString("error converting dict to scriptext map", err);
            pMap->DecRef();
            return false;
        }
    }
    CleanupStack::Pop(pMap);
    liw_variant.Set(pMap);
    return true;
}

static bool
SPyLiwList_FromList(PyObject *list, TLiwVariant &liw_variant)
{
    CLiwDefaultList* plist = CLiwDefaultList::NewL();
    CleanupClosePushL(*plist);
    PyObject *item = NULL;

    TInt n = PyList_Size(list);
    for (TInt i = 0; i < n; i++)
    {
        item = PyList_GetItem(list, i);
        TLiwVariant item_c;
        if(!SPyVariant_FromValue(item, item_c))
        {
            plist->DecRef();
            return false;
        }
        item_c.PushL();
        TRAPD(err, plist->AppendL(item_c));
        CleanupStack::Pop(&item_c);
        if (err != KErrNone)
        {
            SPyLiwErr_SetString("error converting list to scriptext list", err);
            plist->DecRef();
            return false;
        }
    }
    CleanupStack::Pop(plist);
    liw_variant.Set(plist);
    return true;
}

/* Convert the Python object 'value' to LIW variant 'liw_variant' and
 * return `true` if success.
 * */
static bool SPyVariant_FromValue(PyObject *value, TLiwVariant &liw_variant)
{

    PyDateTime_IMPORT;
    if (PyInt_Check(value))
    {
        liw_variant.Set(PyInt_AS_LONG(value));
        return true;
    }

    if (PyFloat_Check(value))
    {
        liw_variant.Set(PyFloat_AS_DOUBLE(value));
        return true;
    }
    if (PyDate_Check(value))
    {
        TTime timeVal = datetime_to_epoch(value);
        if (timeVal == NULL)
        {
            PyErr_SetString(PyExc_TypeError,
                            "Failure in setting the time");
        }
        liw_variant.Set(timeVal);
        return true;
    }
    if (PyLong_Check(value))
    {
        liw_variant.Set((long)PyLong_AsLongLong(value));
        return true;
    }

    if (PyUnicode_Check(value))
    {
        const char *val_ptr = PyUnicode_AS_DATA(value);
        int val_l = PyUnicode_GET_SIZE(value);
        TPtrC val_c((TUint16*)val_ptr, val_l);
        liw_variant.Set(val_c);
        return true;
    }

    if (PyString_Check(value))
    {
        const char *val_ptr = PyString_AsString(value);
        int val_l = PyString_Size(value);
        TPtrC8 val_c((const unsigned char*)val_ptr, val_l);
        liw_variant.Set(val_c);
        return true;
    }

    if (PyDict_Check(value))
        return SPyLiwMap_FromDict(value, liw_variant);

    if (PyList_Check(value))
        return SPyLiwList_FromList(value, liw_variant);

    PyErr_SetString(PyExc_TypeError, "unsupported type");
    return false;
}

/******************** LiwHandle Object *********************/


typedef struct liwhandle {
    PyObject_HEAD
    CLiwServiceHandler *serviceHandler;
    MLiwInterface* interface;
    RCriteriaArray interest;
    CLiwCallback *callbackHandler;
} LiwHandle;

static void
LiwHandle_dealloc(LiwHandle *self)
{
    self->interface->Close();
    TRAPD(err, self->serviceHandler->DetachL(self->interest));
    if (err != KErrNone)
        PyErr_WriteUnraisable((PyObject*)self);

    self->serviceHandler->Reset();
    delete self->serviceHandler;

    self->callbackHandler->Reset();
    delete self->callbackHandler;

    self->ob_type->tp_free((PyObject *)self);
}

static void
Paramlist_cleanup(CLiwGenericParamList *inParamList,
                                   CLiwGenericParamList *outParamList = NULL)
{
    if (inParamList)
        inParamList->Reset();
    if (outParamList)
        outParamList->Reset();
}

int GetErrorCode(CLiwGenericParamList &aOutParamList)
{
    int index = 0;
    const TLiwGenericParam* errNo = aOutParamList.FindFirst(index, KErrCode);
    if (index == KErrNotFound)
        return KErrNone;

    return errNo->Value().AsTInt32();
}


/* Return error message if present in `aOutParamList`. If `aDefaultMsg`
 * is `true`, then a default error message is returned if `aOutParamList`
 * does not contain any error message. */

PyObject* GetErrorMessage(CLiwGenericParamList &aOutParamList,
                                                      bool aDefaultMsg=true)
{
    TInt index = 0;
    const TLiwGenericParam* errMsg = aOutParamList.FindFirst(index,
                                                              KErrMessage);
    if (KErrNotFound == index)
    {
        if (!aDefaultMsg)
            return NULL;

        char *defaultErrMessage = "error executing the requested service";
        return PyString_FromString(defaultErrMessage);
    }

    TLiwVariant value = errMsg->Value();
    PyObject *unicode_str = SPyValue_FromVariant(value);
    value.Reset();
    return PyUnicode_AsASCIIString(unicode_str);
}

extern "C" PyObject *
Call(LiwHandle *self, PyObject *args, PyObject *kwds)
{
    const char *cmd = NULL;
    PyObject *param_py = NULL, *callback = NULL;
    int cmd_l;
    CLiwGenericParamList *inParamList = NULL, *outParamList = NULL;
    static char *kwlist[] = {"service", "service_args", "callback", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "s#O!|O:call",
            kwlist, &cmd, &cmd_l, &PyDict_Type, &param_py, &callback))
    {
        Py_RETURN_NONE;
    }

    if (callback && !PyCallable_Check(callback)) {
        PyErr_SetString(PyExc_TypeError, "callable expected");
        return NULL;
    }

    TRAPD(err, {
        inParamList = &(self->serviceHandler->InParamListL());
        outParamList = &(self->serviceHandler->OutParamListL());
        });
    if (err != KErrNone)
        return SPyLiwErr_SetString("error initializing request service", err);

    TInt index = 0;
    PyObject *key = NULL, *value = NULL;
    while (PyDict_Next(param_py, &index, &key, &value))
    {
        if (!PyString_Check(key))
        {
            Paramlist_cleanup(inParamList);
            PyErr_SetString(PyExc_TypeError, "key should be a string");
            return NULL;
        }
        const char *key_ptr = PyString_AsString(key);
        int key_l = PyString_Size(key);
        TPtrC8 key_c((const unsigned char*)key_ptr, key_l);

        if (0 >= key_l)
        {
            Paramlist_cleanup(inParamList);
            PyErr_SetString(PyExc_KeyError, "key cannot be a null string");
            return NULL;
        }

        TLiwVariant val_new;
        bool res = SPyVariant_FromValue(value, val_new);
        if (!res)
        {
            Paramlist_cleanup(inParamList);
            // No need to set exception as SPyVariant_FromValue()
            // would have set it.
            return NULL;
        }

        val_new.PushL();
        TRAP(err, inParamList->AppendL(TLiwGenericParam(_L8(key_c.Ptr()),
                                                        val_new)));
        CleanupStack::Pop(&val_new);
        if (err != KErrNone)
        {
            Paramlist_cleanup(inParamList);
            return SPyLiwErr_SetString("error creating scriptext input param list", err);
        }
    }

    TPtrC8 req_service((const unsigned char*)cmd, cmd_l);
    TInt cmdOption = 0;
    HBufC8* searchKey;
    TRAP(err, searchKey = HBufC8::NewL(SEARCH_KEY_LEN));
    if (KErrNone != err)
    {
        Paramlist_cleanup(inParamList);
        PyErr_SetString(PyExc_MemoryError, "not able to allocate memory");
        return NULL;
    }
    CleanupStack::PushL(searchKey);

    TPtr8 searchKey_ptr = searchKey->Des();
    searchKey_ptr.Copy(KReturnValue);
    CLiwCallback *callbackObj = NULL;

    if (callback){
        cmdOption |= KLiwOptASyncronous;
        callbackObj = self->callbackHandler;
        searchKey_ptr.Copy(KTransactionID);
    }

    /* LIW requires that when `Cancel` command is issued, cmdOption must
     * have KLiwOptCancel flag set. */
    if(!req_service.Compare(KLiwCancelCmd))
        cmdOption |= KLiwOptCancel;

    TRAP(err, self->interface->ExecuteCmdL(req_service, *(inParamList),
                                           *(outParamList), cmdOption, callbackObj));
    if (err != KErrNone)
    {
        Paramlist_cleanup(inParamList, outParamList);
        CleanupStack::PopAndDestroy(searchKey);
        return SPyLiwErr_SetString("error executing the requested service", err);
    }

    err = GetErrorCode(*outParamList);
    if (err != SErrNone)
    {
        PyObject *errMsg = GetErrorMessage(*outParamList);
        SPyLiwErr_SetString(PyString_AsString(errMsg), err);

        Paramlist_cleanup(inParamList, outParamList);
        CleanupStack::PopAndDestroy(searchKey);
        return NULL;
    }

    index = 0;
    const TLiwGenericParam* item = outParamList->FindFirst(index, searchKey_ptr);
    CleanupStack::PopAndDestroy(searchKey);
    if (index == KErrNotFound)
    {
        if(callback)
            SPyLiwErr_SetString("error retreving the transaction ID");

        Paramlist_cleanup(inParamList, outParamList);
        Py_RETURN_NONE;
    }

    TLiwVariant ret_val = item->Value();
    if (callback)
    {
        Py_INCREF(callback);
        TRAP(err, self->callbackHandler->RegisterCallbackL(ret_val.AsTInt32(),
                                                           callback));
        if (KErrNone != err)
        {
            SPyLiwErr_SetString("error in registering the callback");
            Paramlist_cleanup(inParamList, outParamList);
            Py_DECREF(callback);
            Py_RETURN_NONE;
        }
    }

    PyObject *returnvalue_wrapper = SPyValue_FromVariant(ret_val);
    ret_val.Reset();

    Paramlist_cleanup(inParamList, outParamList);

    return returnvalue_wrapper;
}

static PyMethodDef LiwHandle_methods[] = {
    {"call", (PyCFunction)Call,
                     METH_VARARGS | METH_KEYWORDS, "request for a service" },
    {NULL}  /* Sentinel */
};

extern "C"
PyTypeObject LiwHandleType = {
    PyObject_HEAD_INIT(NULL)
    0,                         /* ob_size */
    "scriptext.scriptextHandle",  /* tp_name */
    sizeof(LiwHandle),             /*tp_basicsize */
    0,                         /* tp_itemsize */
    (destructor)LiwHandle_dealloc, /*tp_dealloc */
    0,                         /* tp_print */
    0,                         /* tp_getattr */
    0,                         /* tp_setattr */
    0,                         /* tp_compare */
    0,                         /* tp_repr */
    0,                         /* tp_as_number */
    0,                         /* tp_as_sequence */
    0,                         /* tp_as_mapping */
    0,                         /* tp_hash */
    0,                         /* tp_call */
    0,                         /* tp_str */
    0,                         /* tp_getattro */
    0,                         /* tp_setattro */
    0,                         /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT, /* tp_flags */
    "ScriptextHandle objects",           /* tp_doc */
    0,               /* tp_traverse */
    0,               /* tp_clear */
    0,               /* tp_richcompare */
    0,               /* tp_weaklistoffset */
    0,               /* tp_iter */
    0,               /* tp_iternext */
    LiwHandle_methods,             /* tp_methods */
    0,             /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    0,      /* tp_init */
    PyType_GenericAlloc,       /* tp_alloc */
    0,                 /* tp_new */
};

TPolicyID GetPolicyIDL()
{
    TPolicyID aPolicyID = -1;
    CRTSecManager* iSession = CRTSecManager::NewL();
    CleanupStack::PushL(iSession);
    //Retrieve the policy ID if its set before
    if (aPolicyID < KErrNone && iSession)
    {
        RFs fileSession;
        User::LeaveIfError(fileSession.Connect());
        CleanupClosePushL(fileSession);
        User::LeaveIfError(fileSession.ShareProtected());
        RFile secPolicyFile;
        User::LeaveIfError(secPolicyFile.Open(fileSession,
                           _L("C:\\data\\python\\AccessPolicy_AliasValid.xml"),
                           EFileShareAny));
        CleanupClosePushL(secPolicyFile);
        aPolicyID = iSession->SetPolicy(secPolicyFile);
        if(aPolicyID > KErrNone)
        {
            //Store the policyID
        }
        CleanupStack::PopAndDestroy(&secPolicyFile);
        CleanupStack::PopAndDestroy(&fileSession);
    }
    CleanupStack::PopAndDestroy(iSession);
    return aPolicyID;
}

CRTSecMgrScriptSession* GetScriptSessionL(bool aRegister, CPyPromptHandler *aPromptHdlr)
{
    CRTSecMgrScriptSession* scriptSession = NULL;

    TPolicyID aPolicyID = GetPolicyIDL();
    CRTSecManager* iSession = CRTSecManager::NewL();
    CleanupStack::PushL(iSession);
    CTrustInfo* iTrust = CTrustInfo::NewL();
    CleanupStack::PushL(iTrust);

    if (aPolicyID < KErrNone || !iSession || !iTrust)
    {
      CleanupStack::PopAndDestroy(2);
        return NULL;
    }

    TInt32 scriptId = 0;
    //Retrive the scriptId if its stored before
    if (!scriptId && !aRegister)//Get the scriptsession without registering the script
        scriptSession =  iSession->GetScriptSessionL(aPolicyID, *iTrust, aPromptHdlr);
    else
    {
        if (!scriptId)//Register the script if scriptId is zero
            scriptId = iSession->RegisterScript(aPolicyID, *iTrust);
        scriptSession = iSession->GetScriptSessionL(aPolicyID, scriptId, aPromptHdlr);
    }

  CleanupStack::PopAndDestroy(2);
    return scriptSession;
}

extern "C" PyObject *
SetSecurityManager(LiwHandle *self, PyObject *args, PyObject *kwds)
{
    PyObject *set_secmgr = Py_False, *lock_set_secmgr = Py_False;
    static char *kwlist[] = {"enabled", "permanent", 0};

    if (!PyArg_ParseTupleAndKeywords(args, kwds,
                                     "O|O:enable_securitymanager",
                                     kwlist,
                                     &set_secmgr, &lock_set_secmgr))
    {
        return NULL;
    }

    if (lock_enable_securitymanager)
        return SPyLiwErr_SetString("no further change allowed");

    if (PyObject_IsTrue(set_secmgr))
        enable_securitymanager = ETrue;
    else
        enable_securitymanager = EFalse;

    if (PyObject_IsTrue(lock_set_secmgr))
        lock_enable_securitymanager = ETrue;

    Py_RETURN_NONE;
}

extern "C" PyObject *
Load_Service(PyObject *self, PyObject *args)
{
    CPyPromptHandler *promptHdlr = NULL;
    char *service = NULL, *data_source = NULL;
    int service_l, data_source_l;
    TInt status;

    if (!PyArg_ParseTuple(args, "s#s#:load",
            &service, &service_l, &data_source, &data_source_l))
    {
        Py_RETURN_NONE;
    }

    TPtrC8 service_ptr((const unsigned char*)service, service_l);
    TPtrC8 data_source_ptr((const unsigned char*)data_source, data_source_l);

    LiwHandle *handle;
    handle = (LiwHandle *) PyType_GenericNew(&LiwHandleType, NULL, NULL);

    if (!handle)
        return NULL;

    CLiwGenericParamList *inParamList = NULL, *outParamList = NULL;
    CLiwCriteriaItem *criteria = NULL;

    //promptHdlr = new CPyPromptHandler;
    //CleanupStack::PushL(promptHdlr);

    TRAPD(err, {
        criteria = CLiwCriteriaItem::NewLC(1, data_source_ptr, service_ptr);
        handle->serviceHandler = CLiwServiceHandler::NewL();
        handle->serviceHandler->Reset();
        handle->callbackHandler = CLiwCallback::NewL();
        criteria->SetServiceClass(TUid::Uid(KLiwClassBase));
        handle->interest.AppendL(criteria);
        CRTSecMgrScriptSession* scriptSession = NULL;
        if (enable_securitymanager)
            scriptSession = GetScriptSessionL(true, promptHdlr);
        status = handle->serviceHandler->AttachL(handle->interest,
                                                     *scriptSession);
        inParamList = &(handle->serviceHandler->InParamListL());
        outParamList = &(handle->serviceHandler->OutParamListL());
        CleanupStack::Pop(criteria);
        });

    if (err != KErrNone)
    {
        delete criteria;
        handle->interest.Reset();
        Paramlist_cleanup(inParamList);
        //CleanupStack::PopAndDestroy(promptHdlr);
        return SPyLiwErr_SetString("error initializing scriptext", err);
    }

    if (status != SErrNone)
    {
        delete criteria;
        handle->interest.Reset();
        Paramlist_cleanup(inParamList);

        PyObject *v = Py_BuildValue("(is)", status,
                                   "error attaching requested services");
        PyErr_SetObject(liw_error, v);
        //CleanupStack::PopAndDestroy(promptHdlr);
        return NULL;
    }

    CleanupStack::PushL(criteria);
    TRAP(err, handle->serviceHandler->ExecuteServiceCmdL (*criteria,
                                                          *inParamList,
                                                          *outParamList));

    CleanupStack::PopAndDestroy(criteria);
    //CleanupStack::PopAndDestroy(promptHdlr);
    criteria = NULL;
    handle->interest.Reset();
    if (err != KErrNone)
    {
        Paramlist_cleanup(inParamList, outParamList);
        return SPyLiwErr_SetString("error loading requested service", err);
    }

    handle->interface = NULL;
    TInt pos = 0;
    outParamList->FindFirst(pos, data_source_ptr);
    if (pos != KErrNotFound)
        handle->interface = (*outParamList)[pos].Value().AsInterface();
    else
    {
        Paramlist_cleanup(inParamList, outParamList);
        return SPyLiwErr_SetString("error fetching requested service");
    }

    Paramlist_cleanup(inParamList, outParamList);

    return (PyObject *) handle;
}

static PyMethodDef liw_methods[] = {
        {"load",   (PyCFunction)Load_Service, METH_VARARGS, NULL},
/*        {"set_securitymanager",   (PyCFunction)SetSecurityManager,
                                     METH_VARARGS | METH_KEYWORDS, NULL}, */
        {NULL,      NULL}
};

PyMODINIT_FUNC initscriptext(void)
{
    PyObject *m, *d;
    m = Py_InitModule("scriptext", liw_methods);
    if (m == NULL)
        return;

    d = PyModule_GetDict(m);
    PyDict_SetItemString(d, "EventStarted",       PyInt_FromLong(KLiwEventStarted));
    PyDict_SetItemString(d, "EventCompleted",     PyInt_FromLong(KLiwEventCompleted));
    PyDict_SetItemString(d, "EventCanceled",      PyInt_FromLong(KLiwEventCanceled));
    PyDict_SetItemString(d, "EventError",         PyInt_FromLong(KLiwEventError));
    PyDict_SetItemString(d, "EventOutParamCheck", PyInt_FromLong(KLiwEventOutParamCheck));
    PyDict_SetItemString(d, "EventInParamCheck",  PyInt_FromLong(KLiwEventInParamCheck));
    PyDict_SetItemString(d, "EventStopped",       PyInt_FromLong(KLiwEventStopped));
    PyDict_SetItemString(d, "EventQueryExit",     PyInt_FromLong(KLiwEventQueryExit));
    PyDict_SetItemString(d, "EventInProgress",    PyInt_FromLong(KLiwEventInProgress));

    liw_error = PyErr_NewException("scriptext.ScriptextError", NULL, NULL);
    if (liw_error == NULL)
            return;

    Py_INCREF(liw_error);
    PyModule_AddObject(m, "ScriptextError", liw_error);

    if (PyType_Ready(&LiwHandleType) < 0 ||
        PyType_Ready(&SPyLiwMapWrapperType) < 0 ||
        PyType_Ready(&SPyLiwListWrapperType) < 0 ||
        PyType_Ready(&SPyLiwIterableWrapperType) < 0)
    {
            return;
    }

    Py_INCREF((PyObject *)&LiwHandleType);
    PyModule_AddObject(m, "ScriptextHandle", (PyObject *)&LiwHandleType);

    Py_INCREF((PyObject *)&SPyLiwMapWrapperType);
    PyModule_AddObject(m, "ScriptextMapWrapper", (PyObject *)&SPyLiwMapWrapperType);

    Py_INCREF((PyObject *)&SPyLiwListWrapperType);
    PyModule_AddObject(m, "ScriptextListWrapper",
                          (PyObject *)&SPyLiwListWrapperType);

    Py_INCREF((PyObject *)&SPyLiwIterableWrapperType);
    PyModule_AddObject(m, "ScriptextIterableWrapper",
                          (PyObject *)&SPyLiwIterableWrapperType);
}
