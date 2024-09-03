# -*- coding: utf-8 -*-
# Copyright 2009-2013, Peter A. Bigot
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain a
# copy of the License at:
#
#            http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""The really ugly code that generates the Python bindings.  This
whole thing is going to be refactored once customized generation makes
it to the top of the task queue."""

import sys
import os.path
import logging
import logging.config
import io
import datetime
import errno

import pyxb
import pyxb.xmlschema as xs
from pyxb.utils import utility, templates, six
from pyxb.utils.utility import repr2to3
from pyxb.binding import basis, datatypes, facets

_log = logging.getLogger(__name__)

def PrefixModule (value, text=None):
    if text is None:
        text = value.__name__
    if value.__module__ == datatypes.__name__:
        return 'pyxb.binding.datatypes.%s' % (text,)
    if value.__module__ == facets.__name__:
        return 'pyxb.binding.facets.%s' % (text,)
    raise ValueError('No standard name for module of value', value)

class ReferenceLiteral (object):
    """Base class for something that requires fairly complex activity
    in order to generate its literal value."""

    # Either a STD or a subclass of _Enumeration_mixin, this is the
    # class in which the referenced object is a member.
    __ownerClass = None

    # The value to be used as a literal for this object
    __literal = None

    def __init__ (self, **kw):
        # NB: Pre-extend __init__
        self.__ownerClass = kw.get('type_definition')

    def setLiteral (self, literal):
        self.__literal = literal
        return literal

    def asLiteral (self):
        return self.__literal

    def _addTypePrefix (self, text, **kw):
        if self.__ownerClass is not None:
            text = '%s.%s' % (pythonLiteral(self.__ownerClass, **kw), text)
        return text

class ReferenceFacetMember (ReferenceLiteral):
    __facetClass = None

    def __init__ (self, **kw):
        variable = kw.get('variable')
        assert (variable is None) or isinstance(variable, facets.Facet)

        if variable is not None:
            kw.setdefault('type_definition', variable.ownerTypeDefinition())
            self.__facetClass = type(variable)
        self.__facetClass = kw.get('facet_class', self.__facetClass)

        super(ReferenceFacetMember, self).__init__(**kw)

        self.setLiteral(self._addTypePrefix('_CF_%s' % (self.__facetClass.Name(),), **kw))

class ReferenceWildcard (ReferenceLiteral):
    __wildcard = None

    def __init__ (self, wildcard, **kw):
        self.__wildcard = wildcard
        super(ReferenceWildcard, self).__init__(**kw)

        template_map = { }
        template_map['Wildcard'] = 'pyxb.binding.content.Wildcard'
        if (xs.structures.Wildcard.NC_any == wildcard.namespaceConstraint()):
            template_map['nc'] = templates.replaceInText('%{Wildcard}.NC_any', **template_map)
        elif isinstance(wildcard.namespaceConstraint(), (set, frozenset)):
            namespaces = []
            for ns in wildcard.namespaceConstraint():
                if ns is None:
                    namespaces.append(None)
                else:
                    namespaces.append(ns.uri())
            template_map['nc'] = 'set([%s])' % (",".join( [ repr2to3(_ns) for _ns in namespaces ]))
        else:
            assert isinstance(wildcard.namespaceConstraint(), tuple)
            ns = wildcard.namespaceConstraint()[1]
            if ns is not None:
                ns = ns.uri()
            template_map['nc'] = templates.replaceInText('(%{Wildcard}.NC_not, %{namespace})', namespace=repr2to3(ns), **template_map)
        template_map['pc'] = wildcard.processContents()
        self.setLiteral(templates.replaceInText('%{Wildcard}(process_contents=%{Wildcard}.PC_%{pc}, namespace_constraint=%{nc})', **template_map))

class ReferenceSchemaComponent (ReferenceLiteral):
    __component = None

    def __init__ (self, component, **kw):
        self.__component = component
        binding_module = kw['binding_module']
        in_class = kw.get('in_class', False)
        super(ReferenceSchemaComponent, self).__init__(**kw)
        rv = binding_module.referenceSchemaComponent(component, in_class)
        self.setLiteral(rv)

class ReferenceNamespace (ReferenceLiteral):
    __namespace = None

    def __init__ (self, **kw):
        self.__namespace = kw['namespace']
        binding_module = kw['binding_module']
        super(ReferenceNamespace, self).__init__(**kw)
        rv = binding_module.referenceNamespace(self.__namespace)
        self.setLiteral(rv)

class ReferenceExpandedName (ReferenceLiteral):
    __expandedName = None

    def __init__ (self, **kw):
        self.__expandedName = kw['expanded_name']
        super(ReferenceExpandedName, self).__init__(**kw)
        self.setLiteral('pyxb.namespace.ExpandedName(%s, %s)' % (pythonLiteral(self.__expandedName.namespace(), **kw), pythonLiteral(self.__expandedName.localName(), **kw)))

class ReferenceFacet (ReferenceLiteral):
    __facet = None

    def __init__ (self, **kw):
        self.__facet = kw['facet']
        super(ReferenceFacet, self).__init__(**kw)
        self.setLiteral('%s._CF_%s' % (pythonLiteral(self.__facet.ownerTypeDefinition(), **kw), self.__facet.Name()))

class ReferenceEnumerationMember (ReferenceLiteral):
    enumerationElement = None

    def __init__ (self, **kw):
        # NB: Pre-extended __init__

        # All we really need is the enumeration element, so we can get
        # its tag, and a type definition or datatype, so we can create
        # the proper prefix.

        # See if we were given a value, from which we can extract the
        # other information.
        value = kw.get('enum_value')
        assert (value is None) or isinstance(value, facets._Enumeration_mixin)

        # Must provide facet_instance, or a value from which it can be
        # obtained.
        facet_instance = kw.get('facet_instance')
        if facet_instance is None:
            assert isinstance(value, facets._Enumeration_mixin)
            facet_instance = value._CF_enumeration
        assert isinstance(facet_instance, facets.CF_enumeration)

        # Must provide the enumeration_element, or a facet_instance
        # and value from which it can be identified.
        self.enumerationElement = kw.get('enumeration_element')
        if self.enumerationElement is None:
            assert value is not None
            self.enumerationElement = facet_instance.elementForValue(value)
        assert isinstance(self.enumerationElement, facets._EnumerationElement)
        assert self.enumerationElement.tag() is not None

        # If no type definition was provided, use the value datatype
        # for the facet.
        kw.setdefault('type_definition', facet_instance.valueDatatype())

        super(ReferenceEnumerationMember, self).__init__(**kw)

        self.setLiteral(self._addTypePrefix(self.enumerationElement.tag(), **kw))

def pythonLiteral (value, **kw):
    # For dictionaries, apply translation to all values (not keys)
    if isinstance(value, six.dictionary_type):
        return ', '.join([ '%s=%s' % (k, pythonLiteral(v, **kw)) for (k, v) in six.iteritems(value) ])

    # For lists, apply translation to all members
    if isinstance(value, six.list_type):
        return [ pythonLiteral(_v, **kw) for _v in value ]

    # ExpandedName is a tuple, but not here
    if isinstance(value, pyxb.namespace.ExpandedName):
        return pythonLiteral(ReferenceExpandedName(expanded_name=value, **kw))

    # For other collection types, do what you do for list
    if isinstance(value, (six.tuple_type, set)):
        return type(value)(pythonLiteral(list(value), **kw))

    # Value is a binding value for which there should be an
    # enumeration constant.  Return that constant.
    if isinstance(value, facets._Enumeration_mixin):
        return pythonLiteral(ReferenceEnumerationMember(enum_value=value, **kw))

    # Value is an instance of a Python binding, e.g. one of the
    # XMLSchema datatypes.  Use its value, applying the proper prefix
    # for the module.
    if isinstance(value, basis.simpleTypeDefinition):
        return PrefixModule(value, value.pythonLiteral())

    if isinstance(value, pyxb.namespace.Namespace):
        return pythonLiteral(ReferenceNamespace(namespace=value, **kw))

    if isinstance(value, type):
        if issubclass(value, basis.simpleTypeDefinition):
            return PrefixModule(value)
        if issubclass(value, facets.Facet):
            return PrefixModule(value)

    if isinstance(value, facets.Facet):
        return pythonLiteral(ReferenceFacet(facet=value, **kw))

    # Treat pattern elements as their value
    if isinstance(value, facets._PatternElement):
        return pythonLiteral(value.pattern)

    # Treat enumeration elements as their value
    if isinstance(value, facets._EnumerationElement):
        return pythonLiteral(value.value())

    # Wildcards expand to a pyxb.binding.content.Wildcard instance
    if isinstance(value, xs.structures.Wildcard):
        return pythonLiteral(ReferenceWildcard(value, **kw))

    # Schema components have a single name through their lifespan
    if isinstance(value, xs.structures._SchemaComponent_mixin):
        return pythonLiteral(ReferenceSchemaComponent(value, **kw))

    # Other special cases
    if isinstance(value, ReferenceLiteral):
        return value.asLiteral()

    # Represent namespaces by their URI
    if isinstance(value, pyxb.namespace.Namespace):
        return repr2to3(value.uri())

    # Standard Python types, including string types
    if isinstance(value, (six.none_type, six.boolean_type, six.float_type, six.integer_types, six.string_types)):
        return pyxb.utils.utility.repr2to3(value)

    raise Exception('Unexpected literal type %s' % (type(value),))

def _GenerateAutomaton (automaton, template_map, containing_state, lines, **kw):
    binding_module = kw['binding_module']
    name = utility.PrepareIdentifier('BuildAutomaton', binding_module.uniqueInModule(), protected=True)
    au_src = []
    au_src.append(templates.replaceInText('''
def %{name} ():
    # Remove this helper function from the namespace after it is invoked
    global %{name}
    del %{name}
    import pyxb.utils.fac as fac
''', name=name))

    def stateSortKey (st):
        if isinstance(st.symbol, xs.structures.ModelGroup):
            return st.symbol.facStateSortKey()
        return st.symbol[0].facStateSortKey()

    def counterConditionSortKey (cc):
        return cc.metadata.facStateSortKey()

    def updateInstructionSortKey (ui):
        return counterConditionSortKey(ui.counterCondition)

    def transitionSortKey (xit):
        # The destination of a transition is not unique; need to
        # differentiate using the update instructions.  Which
        # themselves should be sorted.
        st = xit.consumingState()

        # Transitions into/out-of subautomata might not include a
        # consuming state.  Give those a sort value -1, which python3
        # considers comparable with the non-negative integer sort key
        # used for states.
        ssk = -1
        if st is not None:
            ssk = stateSortKey(st)
        keys = [ ssk ]
        keys.extend(map(updateInstructionSortKey, sorted(xit.updateInstructions, key=updateInstructionSortKey)))
        return tuple(keys)

    au_src.append('    counters = set()')
    counter_map = {}
    sorted_counter_conditions = sorted(automaton.counterConditions, key=counterConditionSortKey)
    for cc in sorted_counter_conditions:
        cc_id = 'cc_%u' % (len(counter_map),)
        counter_map[cc] = cc_id
        au_src.append('    %s = fac.CounterCondition(min=%s, max=%s, metadata=%r)' % (cc_id, repr2to3(cc.min), repr2to3(cc.max), cc.metadata._location()))
        au_src.append('    counters.add(%s)' % (cc_id,))
    state_map = {}
    au_src.append('    states = []')
    sorted_states = sorted(automaton.states, key=stateSortKey)
    for st in sorted_states:
        st_id = 'st_%u' % (len(state_map),)
        state_map[st] = st_id
        if st.subAutomata is not None:
            au_src.append('    sub_automata = []')
            for sa in st.subAutomata:
                au_src.append('    sub_automata.append(%s)' % (_GenerateAutomaton(sa, template_map, st_id, lines, **kw),))
        if st.finalUpdate is None:
            au_src.append('    final_update = None')
        else:
            au_src.append('    final_update = set()')
            for ui in sorted(st.finalUpdate, key=updateInstructionSortKey):
                au_src.append('    final_update.add(fac.UpdateInstruction(%s, %r))' % (counter_map[ui.counterCondition], ui.doIncrement))
        if isinstance(st.symbol, xs.structures.ModelGroup):
            au_src.append('    symbol = %r' % (st.symbol._location(),))
        else:
            (particle, symbol) = st.symbol
            if isinstance(symbol, xs.structures.Wildcard):
                au_src.append(templates.replaceInText('    symbol = pyxb.binding.content.WildcardUse(%{wildcard}, %{location})', wildcard=binding_module.literal(symbol, **kw), location=repr2to3(particle._location())))
            elif isinstance(symbol, xs.structures.ElementDeclaration):
                binding_module.importForDeclaration(symbol)
                au_src.append(templates.replaceInText('    symbol = pyxb.binding.content.ElementUse(%{ctd}._UseForTag(%{field_tag}), %{location})', field_tag=binding_module.literal(symbol.expandedName(), **kw), location=repr2to3(particle._location()), **template_map))
        au_src.append('    %s = fac.State(symbol, is_initial=%r, final_update=final_update, is_unordered_catenation=%r)' % (st_id, st.isInitial, st.isUnorderedCatenation))
        if st.subAutomata is not None:
            au_src.append('    %s._set_subAutomata(*sub_automata)' % (st_id,))
        au_src.append('    states.append(%s)' % (st_id,))
    for st in sorted_states:
        au_src.append('    transitions = []')
        for xit in sorted(st.transitionSet, key=transitionSortKey):
            au_src.append('    transitions.append(fac.Transition(%s, [' % (state_map[xit.destination],))
            sorted_ui = sorted(xit.updateInstructions, key=updateInstructionSortKey)
            au_src.append('        %s ]))' % (',\n        '.join(map(lambda _ui: 'fac.UpdateInstruction(%s, %r)' % (counter_map[_ui.counterCondition], _ui.doIncrement), sorted_ui))))
        au_src.append('    %s._set_transitionSet(transitions)' % (state_map[st],))
    au_src.append('    return fac.Automaton(states, counters, %r, containing_state=%s)' % (automaton.nullable, containing_state))
    lines.extend(au_src)
    return '%s()' % (name,)

def GenerateAutomaton (ctd, **kw):
    aux = _CTDAuxData.Get(ctd)
    binding_module = kw['binding_module']
    template_map = { 'ctd' : binding_module.literal(ctd, **kw) }
    automaton = aux.automaton
    if automaton is None:
        return None
    lines = []
    name = _GenerateAutomaton(automaton, template_map, 'None', lines, **kw)
    return (name, lines)

def _useEnumerationTags (td):
    if td is None:
        return False
    assert isinstance(td, xs.structures.SimpleTypeDefinition)
    ptd = td.baseTypeDefinition()
    python_support = None
    # Atomic types that use strings as their representation
    if (ptd.VARIETY_atomic == ptd.variety()):
        python_support = ptd.primitiveTypeDefinition().pythonSupport()
        return issubclass(python_support, six.string_types)
    # Derivations from anySimpleType use strings too
    if (ptd.VARIETY_absent == ptd.variety()):
        return True
    # Union types?  Yeah, I suppose so.  Though this only applies to
    # members lifted up into the union.
    if (ptd.VARIETY_union == ptd.variety()):
        return True
    # List types have spaces so no tags.
    return False

def GenerateFacets (td, generator, **kw):
    binding_module = kw['binding_module']
    outf = binding_module.bindingIO()
    facet_instances = []
    gen_enum_tag = _useEnumerationTags(td)
    for (fc, fi) in six.iteritems(td.facets()):
        #if (fi is None) or (fi.ownerTypeDefinition() != td):
        #    continue
        if (fi is None) and (fc in td.baseTypeDefinition().facets()):
            # Nothing new here
            continue
        if (fi is not None) and (fi.ownerTypeDefinition() != td):
            # Did this one in an ancestor
            continue
        argset = { }
        is_collection = issubclass(fc, facets._CollectionFacet_mixin)
        if issubclass(fc, facets._LateDatatype_mixin):
            vdt = td
            if fc.LateDatatypeBindsSuperclass():
                vdt = vdt.baseTypeDefinition()
            argset['value_datatype'] = vdt
        if fi is not None:
            if not is_collection:
                argset['value'] = fi.value()
            if isinstance(fi, facets.CF_enumeration):
                argset['enum_prefix'] = fi.enumPrefix()
        facet_var = ReferenceFacetMember(type_definition=td, facet_class=fc, **kw)
        outf.write("%s = %s(%s)\n" % binding_module.literal( (facet_var, fc, argset ), **kw))
        facet_instances.append(binding_module.literal(facet_var, **kw))
        if (fi is not None) and is_collection:
            for i in six.iteritems(fi):
                if isinstance(i, facets._EnumerationElement):
                    if isinstance(i.value(), pyxb.namespace.ExpandedName):
                        enum_config = '%s.addEnumeration(value=%s, tag=%s)' % binding_module.literal( ( facet_var, i.value(), i.tag() ), **kw)
                    else:
                        enum_config = '%s.addEnumeration(unicode_value=%s, tag=%s)' % binding_module.literal( ( facet_var, i.unicodeValue(), i.tag() ), **kw)
                    if gen_enum_tag and (i.tag() is not None):
                        enum_member = ReferenceEnumerationMember(type_definition=td, facet_instance=fi, enumeration_element=i, **kw)
                        outf.write("%s = %s\n" % (binding_module.literal(enum_member, **kw), enum_config))
                        if fi.enumPrefix() is not None:
                            outf.write("%s_%s = %s\n" % (fi.enumPrefix(), i.tag(), binding_module.literal(enum_member, **kw)))
                    else:
                        outf.write("%s\n" % (enum_config,))
                if isinstance(i, facets._PatternElement):
                    outf.write("%s.addPattern(pattern=%s)\n" % binding_module.literal( (facet_var, i.pattern ), **kw))
    if gen_enum_tag and (xs.structures.SimpleTypeDefinition.VARIETY_union == td.variety()):
        # If the union has enumerations of its own, there's no need to
        # inherit anything, because they supersede anything implicitly
        # inherited.
        fi = td.facets().get(facets.CF_enumeration)
        if fi is None:
            # Need to expose any enumerations in members up in this class
            for mtd in td.memberTypeDefinitions():
                if not _useEnumerationTags(mtd):
                    continue
                fi = mtd.facets().get(facets.CF_enumeration)
                if fi is None:
                    continue
                for i in six.iteritems(fi):
                    assert isinstance(i, facets._EnumerationElement)
                    etd = i.enumeration().ownerTypeDefinition()
                    enum_member = ReferenceEnumerationMember(type_definition=td, facet_instance=fi, enumeration_element=i, **kw)
                    outf.write("%-50s%s\n" % ('%s = %s' % binding_module.literal( (enum_member, i.unicodeValue()) ),
                                              '# originally %s.%s' % (binding_module.literal(etd), i.tag())))
    if 2 <= len(facet_instances):
        map_args = ",\n   ".join(facet_instances)
    else:
        map_args = ','.join(facet_instances)
    outf.write("%s._InitializeFacetMap(%s)\n" % (binding_module.literal(td, **kw), map_args))

def _VCAppendAuxInit (vc_source, aux_init, binding_module, kw):
    if vc_source.fixed() is not None:
        aux_init.append('fixed=True')
        aux_init.append('unicode_default=%s' % (binding_module.literal(vc_source.fixed(), **kw),))
    elif vc_source.default() is not None:
        aux_init.append('unicode_default=%s' % (binding_module.literal(vc_source.default(), **kw),))

# If std is a simple type that requires an enumeration mixin, return the
# corresponding facet; otherwise return None.
def simpleTypeOwnedEnumerationFacet (std):
    if not isinstance(std, xs.structures.SimpleTypeDefinition):
        return None
    enum_facet = std.facets().get(facets.CF_enumeration)
    if (enum_facet is not None) and (enum_facet.ownerTypeDefinition() == std):
        return enum_facet
    return None

def GenerateSTD (std, generator):

    binding_module = generator.moduleForComponent(std)
    outf = binding_module.bindingIO()

    class_keywords = frozenset(basis.simpleTypeDefinition._ReservedSymbols)
    class_unique = set()

    kw = { }
    kw['binding_module'] = binding_module
    kw['class_keywords'] = class_keywords
    kw['class_unique'] = class_unique

    parent_classes = [ binding_module.literal(std.baseTypeDefinition(), **kw) ]
    if simpleTypeOwnedEnumerationFacet(std) is not None:
        parent_classes.append('pyxb.binding.basis.enumeration_mixin')

    template_map = { }
    binding_name = template_map['std'] = binding_module.literal(std, **kw)
    if (std.expandedName() is not None) and (std.expandedName().localName() != binding_name):
        _log.warning('Simple type %s renamed to %s', std.expandedName(), binding_name)

    template_map['superclasses'] = ''
    if 0 < len(parent_classes):
        template_map['superclasses'] = ', '.join(parent_classes)
    template_map['expanded_name'] = binding_module.literal(std.expandedName(), **kw)
    if std.expandedName() is not None:
        template_map['qname'] = six.text_type(std.expandedName())
    else:
        template_map['qname'] = '[anonymous]'
    template_map['namespaceReference'] = binding_module.literal(std.bindingNamespace(), **kw)
    template_map['xsd_location'] = repr2to3(std._location())
    if std.annotation() is not None:
        template_map['documentation'] = std.annotation().asDocString()
        template_map['documentation_expr'] = binding_module.literal(std.annotation().text())
    else:
        template_map['documentation'] = ''
        template_map['documentation_expr'] = binding_module.literal(None)

    # @todo: Extensions of LIST will be wrong in below

    common_template = '''
    """%{documentation}"""

    _ExpandedName = %{expanded_name}
    _XSDLocation = %{xsd_location}
    _Documentation = %{documentation_expr}
'''
    if xs.structures.SimpleTypeDefinition.VARIETY_absent == std.variety():
        template = '''
# The ur simple type: %{qname}
class %{std} (%{superclasses}):
''' + common_template
        if not template_map['documentation']:
            template_map['documentation'] = 'The ur simple type.'
    elif xs.structures.SimpleTypeDefinition.VARIETY_atomic == std.variety():
        template = '''
# Atomic simple type: %{qname}
class %{std} (%{superclasses}):
''' + common_template
        if not template_map['documentation']:
            template_map['documentation'] = 'An atomic simple type.'
    elif xs.structures.SimpleTypeDefinition.VARIETY_list == std.variety():
        template = '''
# List simple type: %{qname}
# superclasses %{superclasses}
class %{std} (pyxb.binding.basis.STD_list):
''' + common_template + '''
    _ItemType = %{itemtype}
'''
        template_map['itemtype'] = binding_module.literal(std.itemTypeDefinition(), **kw)
        if not template_map['documentation']:
            template_map['documentation'] = templates.replaceInText('Simple type that is a list of %{itemtype}.', **template_map)
    elif xs.structures.SimpleTypeDefinition.VARIETY_union == std.variety():
        template = '''
# Union simple type: %{qname}
# superclasses %{superclasses}
class %{std} (pyxb.binding.basis.STD_union):
''' + common_template + '''
    _MemberTypes = ( %{membertypes}, )
'''
        template_map['membertypes'] = ", ".join( [ binding_module.literal(_mt, **kw) for _mt in std.memberTypeDefinitions() ])
        if not template_map['documentation']:
            template_map['documentation'] = templates.replaceInText('Simple type that is a union of %{membertypes}.', **template_map)
    else:
        raise pyxb.LogicError("Unhandled STD variety")

    outf.write(templates.replaceInText(template, **template_map))

    GenerateFacets(std, generator, **kw)

    if std.name() is not None:
        outf.write(templates.replaceInText("%{namespaceReference}.addCategoryObject('typeBinding', %{localName}, %{std})\n",
                                           localName=binding_module.literal(std.name(), **kw), **template_map))
    outf.write(templates.replaceInText('_module_typeBindings.%{std} = %{std}\n', **template_map))

def elementDeclarationMap (ed, binding_module, **kw):
    template_map = { }
    template_map['qname'] = six.text_type(ed.expandedName())
    template_map['decl_location'] = repr2to3(ed._location())
    template_map['namespaceReference'] = binding_module.literal(ed.bindingNamespace(), **kw)
    if (ed.SCOPE_global == ed.scope()):
        binding_name = template_map['class'] = binding_module.literal(ed, **kw)
        if ed.expandedName().localName() != binding_name:
            _log.warning('Element %s renamed to %s', ed.expandedName(), binding_name)
        template_map['localName'] = binding_module.literal(ed.name(), **kw)
        template_map['map_update'] = templates.replaceInText("%{namespaceReference}.addCategoryObject('elementBinding', %{localName}, %{class})", **template_map)
    else:
        template_map['scope'] = binding_module.literal(ed.scope(), **kw)
    if ed.annotation() is not None:
        template_map['documentation'] = binding_module.literal(six.text_type(ed.annotation()))
    if ed.abstract():
        template_map['abstract'] = binding_module.literal(ed.abstract(), **kw)
    if ed.nillable():
        template_map['nillable'] = binding_module.literal(ed.nillable(), **kw)
    if ed.default():
        template_map['defaultValue'] = binding_module.literal(ed.default(), **kw)
    template_map['typeDefinition'] = binding_module.literal(ed.typeDefinition(), **kw)
    if ed.substitutionGroupAffiliation():
        template_map['substitution_group'] = binding_module.literal(ed.substitutionGroupAffiliation(), **kw)
    aux_init = []
    for k in ( 'nillable', 'abstract', 'scope', 'documentation' ):
        if k in template_map:
            aux_init.append('%s=%s' % (k, template_map[k]))
    aux_init.append('location=%s' % (template_map['decl_location'],))
    _VCAppendAuxInit(ed, aux_init, binding_module, kw)
    template_map['element_aux_init'] = ''
    if 0 < len(aux_init):
        template_map['element_aux_init'] = ', ' + ', '.join(aux_init)

    return template_map

import pyxb.utils.fac
import operator
import functools

# A Symbol in the term tree is a pair consisting of the containing
# particle (for location information) and one of an
# ElementDeclaration, Wildcard, or tuple of sub-term-trees for All
# model groups.

def BuildTermTree (node):
    """Construct a L{FAC term tree<pyxb.utils.fac.Node>} for a L{particle<xs.structures.Particle>}.

    This translates the XML schema content model of particles, model
    groups, element declarations, and wildcards into a tree expressing
    the corresponding content as a regular expression with numerical
    constraints.

    @param node: An instance of L{xs.structures.Particle}

    @return: An instance of L{pyxb.utils.fac.Node}
    """

    def _generateTermTree_visitor (node, entered, arg):
        """Helper for constructing a L{FAC term tree<pyxb.utils.fac.Node>}.

        This is passed to L{xs.structures.Particle.walkParticleTree}.

        @param node: An instance of L{xs.structures._ParticleTree_mixin}

        @param entered: C{True} entering an interior tree node, C{False}
        leaving an interior tree node, C{None} at a leaf node.

        @param arg: A list of pairs C{(particle, terms)} where C{particle}
        is the L{xs.structures.Particle} instance containing a list of
        L{term trees<pyxb.utils.fac.Node>}.
        """

        if entered is None:
            (parent_particle, terms) = arg.peekNodeTermPair()
            assert isinstance(parent_particle, xs.structures.Particle)
            assert isinstance(node, (xs.structures.ElementDeclaration, xs.structures.Wildcard))
            node._setFacStateSortKey(arg.nextSequenceNumber())
            terms.append(pyxb.utils.fac.Symbol((parent_particle, node)))
        elif entered:
            node._setFacStateSortKey(arg.nextSequenceNumber())
            arg.addNode(node)
        else:
            (xnode, terms) = arg.popNodeTermPair()
            assert xnode == node
            (parent_particle, siblings) = arg.peekNodeTermPair()
            if 1 == len(terms):
                term = terms[0]
                # Either node is a Particle, or it's a single-member model
                # group.  If it's a non-trivial particle we need a
                # numerical constraint; if it's a single-member model
                # group or a trivial particle we can use the term
                # directly.
                if isinstance(node, xs.structures.Particle) and ((1 != node.minOccurs()) or (1 != node.maxOccurs())):
                    term = pyxb.utils.fac.NumericalConstraint(term, node.minOccurs(), node.maxOccurs(), metadata=node)
            else:
                assert isinstance(parent_particle, xs.structures.Particle), 'unexpected %s' % (parent_particle,)
                assert isinstance(node, xs.structures.ModelGroup)
                if node.C_CHOICE == node.compositor():
                    term = pyxb.utils.fac.Choice(*terms, metadata=node)
                elif node.C_SEQUENCE == node.compositor():
                    term = pyxb.utils.fac.Sequence(*terms, metadata=node)
                else:
                    # The quadratic state explosion and need to clone
                    # terms that results from a naive transformation of
                    # unordered catenation to choices among sequences of
                    # nodes and recursively-defined catenation expressions
                    # is not worth the pain.  Create a "symbol" for the
                    # state and hold the alternatives in it.
                    assert node.C_ALL == node.compositor()
                    assert functools.reduce(operator.and_, map(lambda _s: isinstance(_s, pyxb.utils.fac.Node), terms), True)
                    term = pyxb.utils.fac.All(*terms, metadata=node)
            siblings.append(term)

    class TermTreeArg (object):
        __sequenceNumber = None
        __termTreeList = None
        __nodeTermPairs = None
        def __init__ (self, node):
            self.__sequenceNumber = 0
            self.__termTreeList = []
            self.__nodeTermPairs = [ (node, self.__termTreeList) ]

        def termTree (self):
            assert 1 == len(self.__nodeTermPairs)
            assert 1 == len(self.__termTreeList)
            return self.__termTreeList[0]

        def peekNodeTermPair (self):
            return self.__nodeTermPairs[-1]

        def popNodeTermPair (self):
            return self.__nodeTermPairs.pop()

        def addNode (self, node):
            self.__nodeTermPairs.append((node, []))

        def nextSequenceNumber (self):
            rv = self.__sequenceNumber
            self.__sequenceNumber += 1
            return rv

    assert isinstance(node, xs.structures.Particle)
    ttarg = TermTreeArg(node)
    node.walkParticleTree(_generateTermTree_visitor, ttarg)
    term_tree = ttarg.termTree()
    return term_tree

def BuildPluralityData (term_tree):
    """Walk a term tree to determine which element declarations may
    appear multiple times.

    The bindings need to use a list for any Python attribute
    corresponding to an element declaration that can occur multiple
    times in the content model.  The number of occurrences is
    determined by the occurrence constraints on parent particles and
    the compositors of containing model groups.  All this information
    is available in the term tree used for the content model
    automaton.

    @param term_tree: A L{FAC term tree<pyxb.utils.fac.Node>}
    representing the content model for a complex data type.

    @return: Plurality data, as a pair C{(singles, multiples)} where
    C{singles} is a set of base L{element
    declarations<xs.structures.ElementDeclaration>} that are known to
    occur at least once and at most once in a region of the content,
    and C{multiples} is a similar set of declarations that are known
    to potentially occur more than once."""

    def _ttMergeSets (parent, child):
        (p1, pm) = parent
        (c1, cm) = child

        # Anything multiple in the child becomes multiple in the parent.
        pm.update(cm)

        # Anything independently occuring once in both parent and child
        # becomes multiple in the parent.
        pm.update(c1.intersection(p1))

        # Anything that was single in the parent (child) but is now
        # multiple is no longer single.
        p1.difference_update(pm)
        c1.difference_update(pm)

        # Anything that was single in the parent and also single in the
        # child is no longer single in the parent.
        p1.symmetric_difference_update(c1)

    def _ttPrePluralityWalk (node, pos, arg):
        # If there are multiple children, create a new list on which they
        # will be placed.
        if isinstance(node, pyxb.utils.fac.MultiTermNode):
            arg.append([])

    def _ttPostPluralityWalk (node, pos, arg):
        # Initialize a fresh result for this node
        singles = set()
        multiples = set()
        combined = (singles, multiples)
        if isinstance(node, pyxb.utils.fac.MultiTermNode):
            # Get the list of children, and examine
            term_list = arg.pop()
            if isinstance(node, pyxb.utils.fac.Choice):
                # For choice we aggregate the singles and multiples
                # separately.
                for (t1, tm) in term_list:
                    multiples.update(tm)
                    singles.update(t1)
            else:
                # For sequence (ordered or not) we merge the children
                assert isinstance(node, (pyxb.utils.fac.Sequence, pyxb.utils.fac.All))
                for tt in term_list:
                    _ttMergeSets(combined, tt)
        elif isinstance(node, pyxb.utils.fac.Symbol):
            (particle, term) = node.metadata
            if isinstance(term, xs.structures.ElementDeclaration):
                # One instance of the base declaration for the element
                singles.add(term.baseDeclaration())
            elif isinstance(term, xs.structures.Wildcard):
                pass
            else:
                assert isinstance(term, list)
                # Unordered catenation is the same as ordered catenation.
                for tt in term:
                    _ttMergeSets(combined, BuildPluralityData(tt))
        else:
            assert isinstance(node, pyxb.utils.fac.NumericalConstraint)
            # Grab the data for the topmost tree and adjust it based on
            # occurrence data.
            combined = arg[-1].pop()
            (singles, multiples) = combined
            if 0 == node.max:
                # If the node can't match at all, there are no occurrences
                # at all
                multiples.clear()
                singles.clear()
            elif 1 == node.max:
                # If the node can only match once, what we've got is right
                pass
            else:
                # If the node can match multiple times, there are no
                # singles.
                multiples.update(singles)
                singles.clear()
        arg[-1].append(combined)

    # Initialize state with an implied parent that currently has no
    # children
    arg = [[]]
    term_tree.walkTermTree(_ttPrePluralityWalk, _ttPostPluralityWalk, arg)

    # The result term tree is the single child of that implied parent
    assert 1 == len(arg)
    arg = arg[0]
    assert 1 == len(arg)
    return arg[0]

class _CTDAuxData (object):
    """Helper class holding information need in both preparation and generation."""

    contentBasis = None
    termTree = None
    edSingles = None
    edMultiples = None
    automaton = None
    ctd = None

    def __init__ (self, ctd):
        self.ctd = ctd
        ctd.__auxData = self
        self.contentBasis = ctd.contentType()[1]
        if isinstance(self.contentBasis, xs.structures.Particle):
            self.termTree = BuildTermTree(self.contentBasis)
            self.automaton = self.termTree.buildAutomaton()
            (self.edSingles, self.edMultiples) = BuildPluralityData(self.termTree)
        else:
            self.edSingles = set()
            self.edMultiples = set()

    @classmethod
    def Create (cls, ctd):
        return cls(ctd)

    @classmethod
    def Get (cls, ctd):
        return ctd.__auxData

def GenerateCTD (ctd, generator, **kw):
    binding_module = generator.moduleForComponent(ctd)
    outf = binding_module.bindingIO()

    prolog_template = None
    template_map = { }
    binding_name = template_map['ctd'] = binding_module.literal(ctd, **kw)
    if (ctd.expandedName() is not None) and (ctd.expandedName().localName() != binding_name):
        _log.warning('Complex type %s renamed to %s', ctd.expandedName(), binding_name)

    base_type = ctd.baseTypeDefinition()
    content_type_tag = ctd._contentTypeTag()

    template_map['base_type'] = binding_module.literal(base_type, **kw)
    template_map['namespaceReference'] = binding_module.literal(ctd.bindingNamespace(), **kw)
    template_map['expanded_name'] = binding_module.literal(ctd.expandedName(), **kw)
    if ctd.expandedName() is not None:
        template_map['qname'] = six.text_type(ctd.expandedName())
    else:
        template_map['qname'] = '[anonymous]'
    template_map['xsd_location'] = repr2to3(ctd._location())
    template_map['simple_base_type'] = binding_module.literal(None, **kw)
    template_map['contentTypeTag'] = content_type_tag
    template_map['is_abstract'] = repr2to3(not not ctd.abstract())

    content_basis = None
    if (ctd.CT_SIMPLE == content_type_tag):
        content_basis = ctd.contentType()[1]
        template_map['simple_base_type'] = binding_module.literal(content_basis, **kw)
    elif (ctd.CT_MIXED == content_type_tag):
        content_basis = ctd.contentType()[1]
    elif (ctd.CT_ELEMENT_ONLY == content_type_tag):
        content_basis = ctd.contentType()[1]

    if ctd.annotation() is not None:
        template_map['documentation'] = ctd.annotation().asDocString()
    elif isinstance(ctd.owner(), xs.structures.ElementDeclaration) \
      and ctd.owner().annotation() is not None:
        template_map['documentation'] = ctd.owner().annotation().asDocString()
    else:
        template_map['documentation'] = templates.replaceInText("Complex type %{qname} with content type %{contentTypeTag}", **template_map)

    prolog_template = '''
# Complex type %{qname} with content type %{contentTypeTag}
class %{ctd} (%{superclass}):
    """%{documentation}"""
    _TypeDefinition = %{simple_base_type}
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_%{contentTypeTag}
    _Abstract = %{is_abstract}
    _ExpandedName = %{expanded_name}
    _XSDLocation = %{xsd_location}
'''

    # Complex types that inherit from non-ur-type complex types should
    # have their base type as their Python superclass, so pre-existing
    # elements and attributes can be re-used.
    inherits_from_base = True
    template_map['superclass'] = binding_module.literal(base_type, **kw)
    if ctd._isHierarchyRoot():
        inherits_from_base = False
        template_map['superclass'] = 'pyxb.binding.basis.complexTypeDefinition'
        assert base_type.nameInBinding() is not None

    if inherits_from_base:
        prolog_template += '''    _ElementMap = %{superclass}._ElementMap.copy()
    _AttributeMap = %{superclass}._AttributeMap.copy()
'''
    else:
        prolog_template += '''    _ElementMap = {}
    _AttributeMap = {}
'''

    # Support for deconflicting attributes, elements, and reserved symbols
    class_keywords = frozenset(basis.complexTypeDefinition._ReservedSymbols)
    class_unique = set()

    # Deconflict elements first, attributes are lower priority.
    # Expectation is that all elements that have the same tag in the
    # XML are combined into the same instance member, even if they
    # have different types.  Determine what name that should be, and
    # whether there might be multiple instances of elements of that
    # name.
    element_uses = []

    definitions = []

    definitions.append('# Base type is %{base_type}')

    # Retain in the ctd the information about the element
    # infrastructure, so it can be inherited where appropriate in
    # subclasses.

    if isinstance(content_basis, xs.structures.Particle):
        aux = _CTDAuxData.Get(ctd)
        elements = aux.edSingles.union(aux.edMultiples)

        outf.postscript().append("\n\n")
        for ed in sorted(elements, key=lambda _c: _c.schemaOrderSortKey()):
            is_plural = ed in aux.edMultiples
            # @todo Detect and account for plurality change between this and base
            ef_map = ed._templateMap()
            if ed.scope() == ctd:
                ef_map.update(elementDeclarationMap(ed, binding_module, **kw))
                aux_init = []
                ef_map['is_plural'] = repr2to3(is_plural)
                element_uses.append(templates.replaceInText('%{use}.name() : %{use}', **ef_map))
                if 0 == len(aux_init):
                    ef_map['aux_init'] = ''
                else:
                    ef_map['aux_init'] = ', ' + ', '.join(aux_init)
                ef_map['element_binding'] = utility.PrepareIdentifier('%s_elt' % (ef_map['id'],), class_unique, class_keywords, private=True)
                if ed.annotation() is not None:
                    ef_map['documentation'] = binding_module.literal(six.text_type(ed.annotation()))
                else:
                    ef_map['documentation'] = binding_module.literal(None)
            if ed.scope() != ctd:
                definitions.append(templates.replaceInText('''
    # Element %{id} (%{qname}) inherited from %{decl_type_en}''', decl_type_en=six.text_type(ed.scope().expandedName()), **ef_map))
                continue

            binding_module.importForDeclaration(ed)
            if ed.expandedName().localName() != ef_map['id']:
                _log.warning('Element use %s.%s renamed to %s', ctd.expandedName(), ed.expandedName(), ef_map['id'])
            definitions.append(templates.replaceInText('''
    # Element %{qname} uses Python identifier %{id}
    %{use} = pyxb.binding.content.ElementDeclaration(%{name_expr}, '%{id}', '%{key}', %{is_plural}, %{decl_location}, %{aux_init})
''', name_expr=binding_module.literal(ed.expandedName(), **kw), **ef_map))

            definitions.append(templates.replaceInText('''
    %{inspector} = property(%{use}.value, %{use}.set, None, %{documentation})
''', **ef_map))
            outf.postscript().append(templates.replaceInText('''
%{ctd}._AddElement(pyxb.binding.basis.element(%{name_expr}, %{typeDefinition}%{element_aux_init}))
''', name_expr=binding_module.literal(ed.expandedName(), **kw), ctd=template_map['ctd'], **ef_map))

        auto_defn = GenerateAutomaton(ctd, binding_module=binding_module, **kw)
        if auto_defn is not None:
            (automaton_ctor, lines) = auto_defn
            if lines:
                outf.postscript().append("\n".join(lines))
                outf.postscript().append("\n")
            outf.postscript().append(templates.replaceInText('%{ctd}._Automaton = %{automaton_ctor}\n', ctd=template_map['ctd'], automaton_ctor=automaton_ctor))
            outf.postscript().append("\n")

    # Create definitions for all attributes.
    attribute_uses = []

    # name - String value of expanded name of the attribute (attr_tag, attr_ns)
    # name_expr - Python expression for an expanded name identifying the attribute (attr_tag)
    # use - Binding variable name holding AttributeUse instance (attr_name)
    # id - Python identifier for attribute (python_attr_name)
    # key - String used as dictionary key holding instance value of attribute (value_attr_name)
    # inspector - Name of the method used for inspection (attr_inspector)
    # mutator - Name of the method use for mutation (attr_mutator)
    for au in sorted(ctd.attributeUses(), key=lambda _au: _au.attributeDeclaration().schemaOrderSortKey()):
        ad = au.attributeDeclaration()
        assert isinstance(ad.scope(), xs.structures.ComplexTypeDefinition), 'unexpected scope %s' % (ad.scope(),)
        au_map = ad._templateMap()
        if ad.scope() != ctd:
            definitions.append(templates.replaceInText('''
    # Attribute %{id} inherited from %{decl_type_en}''', decl_type_en=six.text_type(ad.scope().expandedName()), **au_map))
            continue
        assert isinstance(au_map, dict)
        aur = au
        while aur.restrictionOf() is not None:
            aur = aur.restrictionOf()
        if au != aur:
            au_map = aur.attributeDeclaration()._templateMap().copy()
            definitions.append(templates.replaceInText('''
    # Attribute %{id} is restricted from parent''', **au_map))

        assert ad.typeDefinition() is not None
        au_map['attr_type'] = binding_module.literal(ad.typeDefinition(), in_class=True, **kw)
        au_map['decl_location'] = repr2to3(ad._location())
        au_map['use_location'] = repr2to3(au._location())

        vc_source = ad
        if au.valueConstraint() is not None:
            vc_source = au
        aux_init = []
        _VCAppendAuxInit(vc_source, aux_init, binding_module, kw)
        if au.required():
            aux_init.append('required=True')
        if au.prohibited():
            aux_init.append('prohibited=True')
        if 0 == len(aux_init):
            au_map['aux_init'] = ''
        else:
            aux_init.insert(0, '')
            au_map['aux_init'] = ', '.join(aux_init)
        if ad.annotation() is not None:
            au_map['documentation'] = binding_module.literal(six.text_type(ad.annotation()))
        else:
            au_map['documentation'] = binding_module.literal(None)

        binding_module.importForDeclaration(ad)
        attribute_uses.append(templates.replaceInText('%{use}.name() : %{use}', **au_map))
        if ad.expandedName().localName() != au_map['id']:
            _log.warning('Attribute %s.%s renamed to %s', ctd.expandedName(), ad.expandedName(), au_map['id'])
        definitions.append(templates.replaceInText('''
    # Attribute %{qname} uses Python identifier %{id}
    %{use} = pyxb.binding.content.AttributeUse(%{name_expr}, '%{id}', '%{key}', %{attr_type}%{aux_init})
    %{use}._DeclarationLocation = %{decl_location}
    %{use}._UseLocation = %{use_location}''', name_expr=binding_module.literal(ad.expandedName(), **kw), **au_map))
        definitions.append(templates.replaceInText('''
    %{inspector} = property(%{use}.value, %{use}.set, None, %{documentation})
''', ctd=template_map['ctd'], **au_map))

    if ctd.attributeWildcard() is not None:
        definitions.append('_AttributeWildcard = %s' % (binding_module.literal(ctd.attributeWildcard(), **kw),))
    if ctd.hasWildcardElement():
        definitions.append('_HasWildcardElement = True')
    template_map['attribute_uses'] = ",\n        ".join(attribute_uses)
    template_map['element_uses'] = ",\n        ".join(element_uses)

    template_map['registration'] = templates.replaceInText('_module_typeBindings.%{ctd} = %{ctd}', **template_map)
    if ctd.name() is not None:
        template_map['registration'] += templates.replaceInText("\n%{namespaceReference}.addCategoryObject('typeBinding', %{localName}, %{ctd})",
                                                                localName=binding_module.literal(ctd.name(), **kw), **template_map)

    template = ''.join([prolog_template,
               "    ", "\n    ".join(definitions), "\n",
               '''    _ElementMap.update({
        %{element_uses}
    })
    _AttributeMap.update({
        %{attribute_uses}
    })
%{registration}

'''])

    outf.write(template, **template_map)

def GenerateED (ed, generator, **kw):
    # Unscoped declarations should never be referenced in the binding.
    assert ed._scopeIsGlobal()

    binding_module = generator.moduleForComponent(ed)
    outf = binding_module.bindingIO()

    template_map = elementDeclarationMap(ed, binding_module, **kw)
    template_map.setdefault('scope', binding_module.literal(None, **kw))
    template_map.setdefault('map_update', '')

    binding_module.importForDeclaration(ed)
    outf.write(templates.replaceInText('''
%{class} = pyxb.binding.basis.element(%{name_expr}, %{typeDefinition}%{element_aux_init})
%{namespaceReference}.addCategoryObject('elementBinding', %{class}.name().localName(), %{class})
''', name_expr=binding_module.literal(ed.expandedName(), **kw), **template_map))

    if ed.substitutionGroupAffiliation() is not None:
        outf.postscript().append(templates.replaceInText('''
%{class}._setSubstitutionGroup(%{substitution_group})
''', **template_map))

def _PrepareSimpleTypeDefinition (std, generator, nsm, module_context):
    std._templateMap()['_unique'] = nsm.uniqueInClass(std)
    if _useEnumerationTags(std):
        enum_facet = simpleTypeOwnedEnumerationFacet(std)
        if enum_facet is not None:
            for ei in six.iteritems(enum_facet):
                assert ei.tag() is None, '%s already has a tag' % (ei,)
                ei._setTag(utility.PrepareIdentifier(ei.unicodeValue(), nsm.uniqueInClass(std)))

def _PrepareComplexTypeDefinition (ctd, generator, nsm, module_context):
    kw = { 'binding_module' : module_context }
    ctd._templateMap()['_unique'] = nsm.uniqueInClass(ctd)
    aux = _CTDAuxData.Create(ctd)
    multiples = aux.edMultiples
    for cd in ctd.localScopedDeclarations():
        _SetNameWithAccessors(cd, ctd, cd in multiples, module_context, nsm, kw)

def _SetNameWithAccessors (component, container, is_plural, binding_module, nsm, kw):
    use_map = component._templateMap()
    class_unique = nsm.uniqueInClass(container)
    assert isinstance(component, xs.structures._ScopedDeclaration_mixin)
    unique_name = utility.PrepareIdentifier(component.expandedName().localName(), class_unique)
    use_map['id'] = unique_name
    use_map['inspector'] = unique_name
    use_map['mutator'] = utility.PrepareIdentifier('set' + unique_name[0].upper() + unique_name[1:], class_unique)
    use_map['use'] = utility.MakeUnique('__' + unique_name.strip('_'), class_unique)
    assert component._scope() == container
    assert component.nameInBinding() is None, 'Use %s but binding name %s for %s' % (use_map['use'], component.nameInBinding(), component.expandedName())
    component.setNameInBinding(use_map['use'])
    key_name = six.u('%s_%s_%s') % (six.text_type(nsm.namespace()), container.nameInBinding(), component.expandedName())
    use_map['key'] = utility.PrepareIdentifier(key_name, class_unique, private=True)
    use_map['qname'] = six.text_type(component.expandedName())
    if isinstance(component, xs.structures.ElementDeclaration) and is_plural:
        use_map['appender'] = utility.PrepareIdentifier('add' + unique_name[0].upper() + unique_name[1:], class_unique)
    return use_map

class BindingIO (object):
    __prolog = None
    __postscript = None
    __templateMap = None
    __stringIO = None
    __bindingFilePath = None
    __bindingFile = None

    def __init__ (self, binding_module, **kw):
        super(BindingIO, self).__init__()
        self.__bindingModule = binding_module
        self.__bindingFilePath = kw['binding_file_path']
        self.__bindingFile = kw['binding_file']
        self.__prolog = []
        self.__postscript = []
        self.__templateMap = kw.copy()
        encoding = kw.get('encoding', pyxb._OutputEncoding)
        self.__templateMap.update({ 'date' : str(datetime.datetime.now()),
                                    'filePath' : self.__bindingFilePath,
                                    'coding' : encoding,
                                    'binding_module' : binding_module,
                                    'binding_tag' : binding_module.bindingTag(),
                                    'pyxbVersion' : pyxb.__version__,
                                    'pyxb_version' : repr2to3(pyxb.__version__),
                                    'pythonVersion' : '.'.join(map(str, sys.version_info))})
        self.__stringIO = io.StringIO()
        if self.__bindingFile:
            prefacet = self.expand('''# %{filePath}
# -*- coding: %{coding} -*-
# PyXB bindings for %{binding_tag}
# Generated %{date} by PyXB version %{pyxbVersion} using Python %{pythonVersion}
%{binding_preface}''', binding_preface=binding_module.bindingPreface())
            self.__bindingFile.write(prefacet.encode(encoding))
            self.__bindingFile.flush()

    def bindingFile (self):
        return self.__bindingFile

    def expand (self, template, **kw):
        tm = self.__templateMap.copy()
        tm.update(kw)
        return templates.replaceInText(template, **tm)

    def appendPrologBoilerplate (self, tm):
        self.prolog().append(self.expand('''# Unique identifier for bindings created at the same time
_GenerationUID = %{generation_uid_expr}

# Version of PyXB used to generate the bindings
_PyXBVersion = %{pyxb_version}
# Generated bindings are not compatible across PyXB versions
if pyxb.__version__ != _PyXBVersion:
    raise pyxb.PyXBVersionError(_PyXBVersion)

# A holder for module-level binding classes so we can access them from
# inside class definitions where property names may conflict.
_module_typeBindings = pyxb.utils.utility.Object()

# Import bindings for namespaces imported into schema
%{aux_imports}

# NOTE: All namespace declarations are reserved within the binding
%{namespace_decls}
''', **tm))

    def write (self, template, **kw):
        txt = self.expand(template, **kw)
        self.__stringIO.write(txt)

    def bindingModule (self):
        return self.__bindingModule
    __bindingModule = None

    def prolog (self):
        return self.__prolog
    def postscript (self):
        return self.__postscript

    def literal (self, *args, **kw):
        kw.update(self.__templateMap)
        return pythonLiteral(*args, **kw)

    def contents (self):
        rv = self.__prolog
        rv.append(self.__stringIO.getvalue())
        rv.extend(self.__postscript)
        return ''.join(rv)

class _ModuleNaming_mixin (object):
    __anonSTDIndex = None
    __anonCTDIndex = None
    __uniqueInModule = None
    __uniqueInClass = None
    __referencedFromClass = None

    _UniqueInModule = set([ 'pyxb', 'sys', '_module_typeBindings' ])
    """Identifiers that are reserved within a module.

    Subclasses extend this with the identifiers they add to the
    module.  Module-level schema-derived identifiers (such as type
    definition and element names) are deconflicted from this set and
    from each other."""

    _ReferencedFromClass = set([ 'pyxb', 'sys', '_module_typeBindings' ])
    """Identifiers defined in module that are accessed unqualified from class.

    These include standard import module names and globals such as
    references to namespaces."""

    __ComponentBindingModuleMap = {}

    def generator (self):
        return self.__generator
    __generator = None

    def __init__ (self, generator, *args, **kw):
        super(_ModuleNaming_mixin, self).__init__(*args, **kw)
        self.__generator = generator
        assert isinstance(self.__generator, Generator)
        self.__anonSTDIndex = 1
        self.__anonCTDIndex = 1
        self.__components = []
        self.__componentNameMap = {}
        self.__uniqueInModule = set()
        self.__referencedFromClass = self._ReferencedFromClass.copy()
        self.__bindingIO = None
        self.__importModulePathMap = {}
        self.__namespaceDeclarations = []
        self.__referencedNamespaces = {}
        self.__uniqueInClass = {}

    def _importModule (self, module):
        assert not isinstance(module, pyxb.namespace.Namespace)
        assert isinstance(module, (_ModuleNaming_mixin, pyxb.namespace.archive.ModuleRecord)), 'Unexpected type %s' % (type(module),)
        if isinstance(module, NamespaceModule):
            if pyxb.namespace.XMLSchema == module.namespace():
                return
            module = module.moduleRecord()
        assert isinstance(module, (pyxb.namespace.archive.ModuleRecord, NamespaceGroupModule))
        if not (module in self.__importModulePathMap):
            module_path = module.modulePath()
            if 'pyxb' == module_path.split('.', 2)[0]:
                assert 'pyxb' in self.uniqueInModule()
                assert 'pyxb' in self.__referencedFromClass
                module_path = None
            else:
                module_path = utility.PrepareIdentifier('ImportedBinding_' + module_path.replace('.', '_'),
                                                        self.uniqueInModule(), protected=True)
                self.__referencedFromClass.add(module_path)
            self.__importModulePathMap[module] = module_path

    def uniqueInClass (self, component):
        rv = self.__uniqueInClass.get(component)
        if rv is None:
            rv = set()
            rv.update(self.__referencedFromClass)
            if isinstance(component, xs.structures.SimpleTypeDefinition):
                rv.update(basis.simpleTypeDefinition._ReservedSymbols)
                if simpleTypeOwnedEnumerationFacet(component) is not None:
                    rv.update(basis.enumeration_mixin._ReservedSymbols)
            else:
                assert isinstance(component, xs.structures.ComplexTypeDefinition)
                if component._isHierarchyRoot():
                    rv.update(basis.complexTypeDefinition._ReservedSymbols)
                else:
                    base_td = component.baseTypeDefinition()
                    base_unique = base_td._templateMap().get('_unique')
                    assert base_unique is not None, 'Base %s of %s has no unique' % (base_td.expandedName(), component.expandedName())
                    rv.update(base_unique)
            self.__uniqueInClass[component] = rv
        return rv

    __referencedNamespaces = None

    def bindingIO (self):
        return self.__bindingIO

    __moduleUID = None
    def moduleUID (self):
        if self.__moduleUID is None:
            self.__moduleUID = pyxb.utils.utility.HashForText(self._moduleUID_vx())
        return self.__moduleUID

    def _moduleUID_vx (self):
        return str(id(self))

    def bindingTag (self):
        """Return a distinct string recorded in the first 4096 bytes of the binding file.

        This is used to ensure uniqueness and avoid overwriting data
        belonging to a different binding.  The return value comprises
        the class-specialized L{_bindingTagPrefix_vx} with the
        L{moduleUID}.
        """
        return '%s:%s' % (self._bindingTagPrefix_vx(), self.moduleUID())

    def _bindingTagPrefix_vx (self):
        raise pyxb.LogicError('Subclass %s does not define _bindingTagPrefix_vx' % (type(self),))

    def bindingPreface (self):
        """Return a block of binding text (comment or code) serving as a preface.

        Normally this should describe the module contents."""
        return self._bindingPreface_vx()
    def _bindingPreface_vx (self):
        return ''

    def moduleContents (self):
        template_map = {}
        aux_imports = []
        for (mr, as_path) in six.iteritems(self.__importModulePathMap):
            assert self != mr
            if as_path is not None:
                aux_imports.append('import %s as %s' % (mr.modulePath(), as_path))
            else:
                aux_imports.append('import %s' % (mr.modulePath(),))
        template_map['aux_imports'] = "\n".join(aux_imports)
        template_map['namespace_decls'] = "\n".join(self.__namespaceDeclarations)
        template_map['module_uid'] = self.moduleUID()
        template_map['generation_uid_expr'] = repr2to3(self.generator().generationUID())
        self._finalizeModuleContents_vx(template_map)
        return self.__bindingIO.contents()

    def modulePath (self):
        return self.__modulePath
    def _setModulePath (self, path_data):
        (binding_file_path, binding_file, module_path) = path_data
        self.__bindingFilePath = binding_file_path
        self.__bindingFile = binding_file
        if module_path is None:
            module_path = self.moduleRecord().modulePath()
        if module_path is not None:
            self.__modulePath = module_path
        kw = self._initialBindingTemplateMap()
        self.__bindingIO = BindingIO(self, binding_file=binding_file, binding_file_path=binding_file_path, **kw)
    __modulePath = None

    def pathFromImport (self, module, name):
        """Python code reference to an object in an imported module"""
        if isinstance(module, NamespaceModule):
            module = module.moduleRecord()
        as_path = self.__importModulePathMap[module]
        if as_path is None:
            as_path = module.modulePath()
        return '%s.%s' % (as_path, name)

    def bindingFile (self):
        return self.__bindingFile
    __bindingFile = None
    __bindingFilePath = None

    def _initializeUniqueInModule (self, unique_in_module):
        self.__uniqueInModule = set(unique_in_module)

    def uniqueInModule (self):
        return self.__uniqueInModule

    @classmethod
    def BindComponentInModule (cls, component, module):
        cls.__ComponentBindingModuleMap[component] = module
        return module

    @classmethod
    def ComponentBindingModule (cls, component):
        return cls.__ComponentBindingModuleMap.get(component)

    @classmethod
    def _RecordModule (cls, module):
        cls.__RecordModuleMap[module.moduleRecord()] = module
        return module
    @classmethod
    def _ForRecord (cls, module_record):
        return cls.__RecordModuleMap.get(module_record)
    __RecordModuleMap = { }

    def _bindComponent (self, component):
        kw = {}
        rv = component.bestNCName()
        if rv is None:
            if isinstance(component, xs.structures.ComplexTypeDefinition):
                rv = utility.PrepareIdentifier('CTD_ANON', self.uniqueInClass(component), protected=True)
            elif isinstance(component, xs.structures.SimpleTypeDefinition):
                rv = utility.PrepareIdentifier('STD_ANON', self.uniqueInClass(component), protected=True)
            else:
                assert False
            kw['protected'] = True
        rv = utility.PrepareIdentifier(rv, self.__uniqueInModule, kw)
        assert not component in self.__componentNameMap
        self.__components.append(component)
        self.__componentNameMap[component] = rv
        return rv
    def nameInModule (self, component):
        return self.__componentNameMap.get(component)

    def referenceSchemaComponent (self, component, in_class=False):
        origin = component._objectOrigin()
        assert origin is not None
        module_record = origin.moduleRecord()
        assert module_record is not None
        if self.generator().generationUID() != module_record.generationUID():
            self._importModule(module_record)
            return self.pathFromImport(module_record, component.nameInBinding())
        component_module = _ModuleNaming_mixin.ComponentBindingModule(component)
        assert component_module is not None, 'No binding module for %s from %s in %s as %s' % (component, module_record, self.moduleRecord(), component.nameInBinding())
        name = component_module.__componentNameMap.get(component)
        if name is None:
            assert isinstance(self, NamespaceModule) and (self.namespace() == component.bindingNamespace())
            name = component.nameInBinding()
        if self != component_module:
            self._importModule(component_module)
            name = self.pathFromImport(component_module, name)
        elif in_class:
            name = '_module_typeBindings.%s' %(name,)
        return name

    def _referencedNamespaces (self): return self.__referencedNamespaces

    def defineNamespace (self, namespace, name, definition=None, **kw):
        rv = self.__referencedNamespaces.get(namespace)
        assert rv is None, 'Module %s already has reference to %s' % (self, namespace)
        # All module-level namespace declarations are reserved.
        # Some may have a protected name.  The unprotected name
        # shall always begin with 'Namespace'.  These names may
        # be referenced from class implementations as well.
        assert name.startswith('Namespace'), 'unexpected %s naming %s' % (name, namespace)
        name = utility.PrepareIdentifier(name, self.__uniqueInModule, **kw)
        self.__referencedFromClass.add(name)
        if definition is None:
            if namespace.isAbsentNamespace():
                definition = 'pyxb.namespace.CreateAbsentNamespace()'
            else:
                definition = 'pyxb.namespace.NamespaceForURI(%s, create_if_missing=True)' % (repr2to3(namespace.uri()),)
        self.__namespaceDeclarations.append('%s = %s' % (name, definition))
        self.__namespaceDeclarations.append("%s.configureCategories(['typeBinding', 'elementBinding'])" % (name,))
        self.__referencedNamespaces[namespace] = name
        return name

    def referenceNamespace (self, namespace):
        rv = self.__referencedNamespaces.get(namespace)
        if rv is None:
            assert not (isinstance(self, NamespaceModule) and (self.namespace() == namespace))
            assert namespace.isBuiltinNamespace() or not namespace.isUndeclaredNamespace()
            if namespace.isBuiltinNamespace():
                rv = namespace.builtinNamespaceRepresentation()
            if rv is None:
                # Not the local namespace or a built-in.  Give it a
                # local name, potentially derived from its prefix.
                # Then try to find an existing import that defines the
                # namespace.  Then define the local name within the
                # binding, either as a reference to a namespace
                # reachable from an import or by doing a runtime
                # lookup from the namespace URI if somehow no provider
                # has been imported.  (This last case should apply
                # only to namespace group modules.)
                if namespace.prefix():
                    nsn = 'Namespace_%s' % (namespace.prefix(),)
                else:
                    nsn = 'Namespace'
                nsdef = None
                for im in six.iterkeys(self.__importModulePathMap):
                    if isinstance(im, pyxb.namespace.archive.ModuleRecord):
                        if im.namespace() == namespace:
                            nsdef = self.pathFromImport(im, 'Namespace')
                            break
                    elif isinstance(im, NamespaceGroupModule):
                        pass
                    else:
                        assert False, 'unexpected import from type %s %s' % (type(im), im,)
                # If we failed to identify the namespace in an existing import,
                # and this module is not a namespace group which includes the
                # namespace as part of its content, something went wrong.
                if (nsdef is None) and not (isinstance(self, NamespaceGroupModule) and self.moduleForNamespace(namespace) is not None):
                    # This can happen if we've got a QName for some namespace for which
                    # we don't have any information.  That's actually OK, so just go
                    # ahead and define a namespace we can reference.
                    pass

                rv =  self.defineNamespace(namespace, nsn, nsdef, protected=True)
                assert 0 < len(self.__namespaceDeclarations)
            self.__referencedNamespaces[namespace] = rv
        return rv

    def importForDeclaration (self, decl):
        """Import the binding from which the declaration came.

        Figure out where the declaration came from.  If it's not part
        of this binding, make sure we import the binding associated
        with the schema from which it came.  We need that, if not for
        something in the declaration itself, at least to be able to
        get the Namespace for the declaration's name.  None of this is
        relevant if the declaration has no namespace."""
        sdecl = decl
        while sdecl._cloneSource() is not None:
            sdecl = sdecl._cloneSource()
        assert decl.expandedName() == sdecl.expandedName()
        ns = decl.expandedName().namespace()
        if ns is None:
            return
        mr = sdecl._objectOrigin().moduleRecord()
        if isinstance(self, NamespaceModule):
            need_import = self.moduleRecord().modulePath() != mr.modulePath()
        elif isinstance(self, NamespaceGroupModule):
            need_import = True
            for nm in self.namespaceModules():
                if nm.moduleRecord().modulePath() == mr.modulePath():
                    need_import = False
                    break
        else:
            raise pyxb.LogicError('Unhandled module naming', self)
        if need_import:
            self._importModule(mr)

    def literal (self, *args, **kw):
        return self.__bindingIO.literal(*args, **kw)

    def addImportsFrom (self, module):
        _log.info('Importing to %s from %s', self, module)
        self._importModule(module)
        for c in self.__components:
            local_name = self.nameInModule(c)
            assert local_name is not None
            rem_name = module.nameInModule(c)
            if rem_name is None:
                continue
            aux = ''
            if local_name != rem_name:
                aux = ' as %s' % (local_name,)
            self.__bindingIO.write("from %s import %s%s # %s\n" % (module.modulePath(), rem_name, aux, c.expandedName()))

    def writeToModuleFile (self):
        if self.bindingFile():
            self.bindingFile().write(self.moduleContents().encode(pyxb._OutputEncoding))
            self.bindingFile().close()
            _log.info('Saved binding source to %s', self.__bindingFilePath)
        else:
            _log.info('No binding file for %s', self)

class NamespaceModule (_ModuleNaming_mixin):
    """This class represents a Python module that holds all the
    declarations belonging to a specific namespace."""

    def namespace (self):
        return self.__namespace
    __namespace = None

    def moduleRecord (self):
        return self.__moduleRecord
    __moduleRecord = None

    def namespaceGroupModule (self):
        return self.__namespaceGroupModule
    def setNamespaceGroupModule (self, namespace_group_module):
        self.__namespaceGroupModule = namespace_group_module
    __namespaceGroupModule = None

    _UniqueInModule = _ModuleNaming_mixin._UniqueInModule.copy()
    _UniqueInModule.update([ 'CreateFromDOM', 'CreateFromDocument' ])

    def namespaceGroupHead (self):
        return self.__namespaceGroupHead
    __namespaceGroupHead = None
    __namespaceGroup = None

    def componentsInNamespace (self):
        return self.__components
    __components = None

    @classmethod
    def ForComponent (cls, component):
        return cls.__ComponentModuleMap.get(component)
    __ComponentModuleMap = { }

    def _bindingTagPrefix_vx (self):
        return 'NM'

    def _bindingPreface_vx (self):
        ns = self.namespace()
        rvl = ['# Namespace %s' % (ns,)]
        if ns.prefix() is not None:
            rvl.append(' [xmlns:%s]' % (ns.prefix(),))
        rvl.append('\n')
        return ''.join(rvl)

    def _moduleUID_vx (self):
        if self.namespace().isAbsentNamespace():
            return 'Absent'
        return six.text_type(self.namespace())

    def namespaceGroupMulti (self):
        return 1 < len(self.__namespaceGroup)

    def __init__ (self, generator, module_record, mr_scc, components=None, **kw):
        super(NamespaceModule, self).__init__(generator, **kw)
        self._initializeUniqueInModule(self._UniqueInModule)
        self.__moduleRecord = module_record
        self.__namespace = self.__moduleRecord.namespace()
        self.defineNamespace(self.__namespace, 'Namespace')
        self._RecordModule(self)
        self.__components = components
        # wow! fromkeys actually IS useful!
        if self.__components is not None:
            self.__ComponentModuleMap.update(dict.fromkeys(self.__components, self))
        self.__namespaceBindingNames = {}
        self.__componentBindingName = {}
        self._setModulePath(generator.modulePathData(self))

    def _initialBindingTemplateMap (self):
        kw = { 'moduleType' : 'namespace'
             , 'targetNamespace' : repr2to3(self.__namespace.uri())
             , 'namespaceURI' : self.__namespace.uri()
             , 'namespaceReference' : self.referenceNamespace(self.__namespace)
             }
        return kw

    def _finalizeModuleContents_vx (self, template_map):
        template_map['_TextType'] = '_six.text_type'
        self.bindingIO().prolog().append('''
from __future__ import unicode_literals
import pyxb
import pyxb.binding
import pyxb.binding.saxer
import io
import pyxb.utils.utility
import pyxb.utils.domutils
import sys
import pyxb.utils.six as _six
''')
        self.bindingIO().appendPrologBoilerplate(template_map)
        self.bindingIO().prolog().append(self.bindingIO().expand('''
def CreateFromDocument (xml_text, default_namespace=None, location_base=None):
    """Parse the given XML and use the document element to create a
    Python instance.

    @param xml_text An XML document.  This should be data (Python 2
    str or Python 3 bytes), or a text (Python 2 unicode or Python 3
    str) in the L{pyxb._InputEncoding} encoding.

    @keyword default_namespace The L{pyxb.Namespace} instance to use as the
    default namespace where there is no default namespace in scope.
    If unspecified or C{None}, the namespace of the module containing
    this function will be used.

    @keyword location_base: An object to be recorded as the base of all
    L{pyxb.utils.utility.Location} instances associated with events and
    objects handled by the parser.  You might pass the URI from which
    the document was obtained.
    """

    if pyxb.XMLStyle_saxer != pyxb._XMLStyle:
        dom = pyxb.utils.domutils.StringToDOM(xml_text)
        return CreateFromDOM(dom.documentElement, default_namespace=default_namespace)
    if default_namespace is None:
        default_namespace = Namespace.fallbackNamespace()
    saxer = pyxb.binding.saxer.make_parser(fallback_namespace=default_namespace, location_base=location_base)
    handler = saxer.getContentHandler()
    xmld = xml_text
    if isinstance(xmld, %{_TextType}):
        xmld = xmld.encode(pyxb._InputEncoding)
    saxer.parse(io.BytesIO(xmld))
    instance = handler.rootObject()
    return instance

def CreateFromDOM (node, default_namespace=None):
    """Create a Python instance from the given DOM node.
    The node tag must correspond to an element declaration in this module.

    @deprecated: Forcing use of DOM interface is unnecessary; use L{CreateFromDocument}."""
    if default_namespace is None:
        default_namespace = Namespace.fallbackNamespace()
    return pyxb.binding.basis.element.AnyCreateFromDOM(node, default_namespace)

''', **template_map))

    __components = None
    __componentBindingName = None

    def bindComponent (self, component):
        ns_name = self._bindComponent(component)
        component.setNameInBinding(ns_name)
        binding_module = self
        if self.__namespaceGroupModule:
            self.__namespaceGroupModule._bindComponent(component)
            binding_module = self.__namespaceGroupModule
        return _ModuleNaming_mixin.BindComponentInModule(component, binding_module)

    def __str__ (self):
        return 'NM:%s@%s' % (self.namespace(), self.modulePath())

class NamespaceGroupModule (_ModuleNaming_mixin):
    """This class represents a Python module that holds all the
    declarations belonging to a set of namespaces which have
    interdependencies."""

    def namespaceModules (self):
        return self.__namespaceModules
    __namespaceModules = None

    def moduleForNamespace (self, namespace):
        for nm in self.__namespaceModules:
            if nm.namespace() == namespace:
                return nm
        return None

    __components = None
    __componentBindingName = None
    __uniqueInModule = None

    __UniqueInGroups = set()

    _GroupPrefix = '_group'

    def __init__ (self, generator, namespace_modules, **kw):
        super(NamespaceGroupModule, self).__init__(generator, **kw)
        assert 1 < len(namespace_modules)
        self.__namespaceModules = namespace_modules
        self.__namespaceGroupHead = namespace_modules[0].namespaceGroupHead()
        self._initializeUniqueInModule(self._UniqueInModule)
        self._setModulePath(generator.modulePathData(self))

    def _initialBindingTemplateMap (self):
        kw = { 'moduleType' : 'namespaceGroup' }
        return kw

    def _bindingTagPrefix_vx (self):
        return 'NGM'

    def _bindingPreface_vx (self):
        rvl = ['# Group contents:\n' ]
        for nsm in self.namespaceModules():
            rvl.append(nsm.bindingPreface())
        rvl.append('\n')
        return ''.join(rvl)

    def _finalizeModuleContents_vx (self, template_map):
        self.bindingIO().prolog().append('''
from __future__ import unicode_literals
import pyxb
import pyxb.binding
import pyxb.utils.utility
import pyxb.utils.six as _six
''')
        self.bindingIO().appendPrologBoilerplate(template_map)

    def _moduleUID_vx (self):
        nss = []
        for nsm in self.namespaceModules():
            ns = nsm.namespace()
            if ns.isAbsentNamespace():
                nss.append('Absent')
            else:
                nss.append(six.text_type(ns))
        nss.sort()
        return six.u(';').join(nss)

    def __str__ (self):
        return 'NGM:%s' % (self.modulePath(),)


def GeneratePython (schema_location=None,
                    schema_text=None,
                    namespace=None,
                    module_prefix_elts=[],
                    **kw):

    generator = Generator(allow_absent_module=True, generate_to_files=False, **kw)
    if schema_location is not None:
        generator.addSchemaLocation(schema_location)
    elif schema_text is not None:
        generator.addSchema(schema_text)
    modules = generator.bindingModules()

    assert 1 == len(modules), '%s produced %d modules: %s' % (namespace, len(modules), six.u(' ').join([ six.text_type(_m) for _m in modules]))
    return modules.pop().moduleContents()

import optparse
import re

class Generator (object):
    """Configuration and data for a single binding-generation action."""

    _DEFAULT_bindingRoot = '.'
    def bindingRoot (self):
        """The directory path into which generated bindings will be written.
        @rtype: C{str}"""
        return self.__bindingRoot
    def setBindingRoot (self, binding_root):
        self.__bindingRoot = binding_root
        return self
    __bindingRoot = None

    def __moduleFilePath (self, module_elts, inhibit_extension=False):
        if isinstance(module_elts, six.string_types):
            module_elts = module_elts.split('.')
        else:
            module_elts = module_elts[:]
        assert 0 < len(module_elts)
        if not inhibit_extension:
            assert not module_elts[-1].endswith('.py')
            module_elts[-1] = '%s.py' % (module_elts[-1],)
        return os.path.join(self.bindingRoot(), *module_elts)

    def generateToFiles (self):
        return self.__generateToFiles
    __generateToFiles = None

    def modulePathData (self, module):
        # file system path to where the bindings are written
        # module path from which the bindings are normally imported
        # file object into which bindings are written

        module_path = None
        if isinstance(module, NamespaceModule):
            mr = module.moduleRecord()
            if mr is None:
                return ('/dev/null', None, None)
            if self.generationUID() != mr.generationUID():
                return ('/dev/null', None, None)
            if not self.generateToFiles():
                return ('/dev/null', None, None)
            if mr.namespace().isBuiltinNamespace() and (not self.allowBuiltinGeneration()):
                return ('/dev/null', None, None)
            module_path = mr.modulePath()
            assert module_path is not None, 'No path specified for module %s' % (mr,)
            #if pyxb.namespace.XMLSchema != ns:
            #    return ('/dev/null', None, None)
            #module_path="bogus.xsd"
            module_elts = module_path.split('.')
            if self.writeForCustomization():
                import_file_path = self.__moduleFilePath(module_elts)
                module_elts.insert(-1, 'raw')
                if not os.path.exists(import_file_path):
                    raw_module_path = '.'.join(module_elts)
                    fd = pyxb.utils.utility.OpenOrCreate(import_file_path)
                    impt = '''# -*- coding: utf-8 -*-
from %s import *
'''  % (raw_module_path,)
                    impd = impt.encode('utf-8')
                    fd.write(impd)
                    fd.close()
            binding_file_path = self.__moduleFilePath(module_elts)
            try:
                binding_file = pyxb.utils.utility.OpenOrCreate(binding_file_path, tag=module.moduleUID())
            except OSError as e:
                if errno.EEXIST == e.errno:
                    raise pyxb.BindingGenerationError('Target file %s for module %s bindings exists with other content' % (binding_file_path, mr))
                raise
        elif isinstance(module, NamespaceGroupModule):
            if not self.generateToFiles():
                raise pyxb.BindingGenerationError('Generation of namespace groups requires generate-to-files')
            module_elts = []
            if self.modulePrefix():
                module_elts.extend(map(utility.MakeModuleElement, self.modulePrefix().split('.')))
            if self.writeForCustomization():
                module_elts.append('raw')
            in_use = set()
            while True:
                module_elts.append(pyxb.utils.utility.PrepareIdentifier('nsgroup', in_use, protected=True))
                try:
                    binding_file_path = self.__moduleFilePath(module_elts)
                    _log.info('Attempting group %s uid %s at %s', module, module.moduleUID(), binding_file_path)
                    binding_file = pyxb.utils.utility.OpenOrCreate(binding_file_path, tag=module.moduleUID())
                    break
                except OSError as e:
                    if errno.EEXIST != e.errno:
                        raise
                module_elts.pop()
            module_path = '.'.join(module_elts)
        else:
            assert False
        if self.generateToFiles():
            for n in range(len(module_elts)-1):
                sub_path = self.__moduleFilePath(module_elts[:1+n], inhibit_extension=True)
                init_path = os.path.join(sub_path, '__init__.py')
                if not os.path.exists(init_path):
                    open(init_path, 'w')
        return (binding_file_path, binding_file, module_path)

    def schemaRoot (self):
        """The directory from which entrypoint schemas specified as
        relative file paths will be read."""
        return self.__schemaRoot
    def setSchemaRoot (self, schema_root):
        if not schema_root.endswith(os.sep):
            schema_root = schema_root + os.sep
        self.__schemaRoot = schema_root
        return self
    __schemaRoot = None

    def schemaStrippedPrefix (self):
        """Optional string that is stripped from the beginning of
        schemaLocation values before loading from them.

        This applies only to the values of schemaLocation attributes
        in C{import} and C{include} elements.  Its purpose is to
        convert absolute schema locations into relative ones to allow
        offline processing when all schema are available in a local
        directory.  See C{schemaRoot}.
        """
        return self.__schemaStrippedPrefix
    def setSchemaStrippedPrefix (self, schema_stripped_prefix):
        self.__schemaStrippedPrefix = schema_stripped_prefix
        return self
    __schemaStrippedPrefix = None

    def locationPrefixRewriteMap (self):
        """Optional map to rewrite schema locations.

        This applies only to the values of schemaLocation attributes
        in C{import} and C{include} elements.  Its purpose is to
        convert remote or absolute schema locations into local or
        relative ones to allow offline processing when all schema are
        available in a local directory.  See C{schemaRoot}.
        """
        return self.__locationPrefixRewriteMap
    def setLocationPrefixRewriteMap (self, location_prefix_rewrite_map):
        self.__locationPrefixMap.clear()
        self.__locationPrefixMap.update(location_prefix_rewrite_map)
        return self
    def addLocationPrefixRewrite (self, prefix, substituent):
        """Add a rewrite entry for schema locations.

        @param prefix : A text prefix that should be removed from
        schema location URIs.

        @param substituent : The text prefix that should replace
        C{prefix} as a prefix in a schema location URI.
        """

        self.__locationPrefixRewriteMap[prefix] = substituent
        return self
    def argAddLocationPrefixRewrite (self, prefix_rewrite):
        """Add a rewrite entry for schema locations.

        Parameter values are strings of the form C{pfx=sub}.  The
        effect is that a schema location that begins with C{pfx} is
        rewritten so that it instead begins with C{sub}."""
        try:
            (prefix, substituent) = prefix_rewrite.split('=', 1)
        except:
            raise
        self.addLocationPrefixRewrite(prefix, substituent)
    __locationPrefixMap = {}

    def schemaLocationList (self):
        """A list of locations from which entrypoint schemas are to be
        read.

        The values in the list are either URIs, or tuples consisting
        of a value and a callable which, when passed the generator
        object and the value, will return a
        L{pyxb.xmlschema.structures.Schema} instance.  See
        L{addSchemaLocation}.

        See also L{addSchemaLocation} and L{schemas}.
        """
        return self.__schemaLocationList
    def setSchemaLocationList (self, schema_location_list):
        self.__schemaLocationList[:] = []
        self.__schemaLocationList.extend(schema_location_list)
        return self
    def addSchemaLocation (self, schema_location, converter=None):
        """Add the location of an entrypoint schema.

        @param schema_location: The location of the schema.  This
        should be a URL; if the schema location does not have a URL
        scheme (e.g., C{http:}), it is assumed to be a file, and if it
        is not an absolute path is located relative to the
        C{schemaRoot}.

        @keyword converter: Optional callable that will be invoked
        with the generator instance and the schema location, and is
        expected to return a L{pyxb.xmlschema.structures.Schema}
        instance.  If absent, the contents of the location are
        converted directly.

        @note: The C{converter} argument derives from WSDL support: we
        need to add to the sequence of schema locations a URI of
        something that will not parse as a schema, but does have inner
        material that can if treated properly.  "Treated properly" may
        include having the archive path and other namespace
        manipulations configured before anything is done to it.
        """
        self.__schemaLocationList.append( (schema_location, converter) )
        return self
    def argAddSchemaLocation (self, schema_location):
        """Add the location of an entrypoint schema.  The provided
        value should be a URL; if it does not have a URL scheme (e.g.,
        C{http:}), it is assumed to be a file, and if it is not an
        absolute path is located relative to the C{schemaRoot}."""
        self.addSchemaLocation(schema_location)
    __schemaLocationList = None

    def schemas (self):
        """Schema for which bindings should be generated.

        These may be L{Schema<pyxb.xmlschema.structures.Schema>}
        instances, or strings; the latter is preferred, and is parsed
        into a Schema instance when required.

        This is the list of entrypoint schemas for binding generation.
        Values in L{schemaLocationList} are read and converted into
        schema, then appended to this list.  Values from L{moduleList}
        are applied starting with the first schema in this list.
        """
        return self.__schemas[:]
    def setSchemas (self, schemas):
        self.__schemas[:] = []
        self.__schemas.extend(schemas)
        return self
    def addSchema (self, schema):
        self.__schemas.append(schema)
        return self
    __schemas = None

    def namespaces (self):
        """The set of L{namespaces<pyxb.namespace.Namespace>} for
        which bindings will be generated.

        This is the set of namespaces read from entrypoint schema,
        closed under reference to namespaces defined by schema import.

        @rtype: C{set}
        """
        return self.__namespaces.copy()
    def setNamespaces (self, namespace_set):
        self.__namespaces.clear()
        self.__namespaces.update(namespace_set)
        return self
    def addNamespace (self, namespace):
        self.__namespaces.add(namespace)
        return self
    __namespaces = None

    def moduleList (self):
        """A list of module names to be applied in order to the namespaces of entrypoint schemas"""
        return self.__moduleList[:]
    def _setModuleList (self, module_list):
        self.__moduleList[:] = []
        self.__moduleList.extend(module_list)
        return self

    def addModuleName (self, module_name):
        """Add a module name corresponding to an entrypoint schema.

        The namespace defined by the corresponding schema will be
        written to a binding using the given module name, adjusted by
        L{modulePrefix}."""
        self.__moduleList.append(module_name)
        return self
    __moduleList = None

    def modulePrefix (self):
        """The prefix for binding modules.

        The base name for the module holding a binding is taken from
        the moduleList, moduleMap, or an XMLNS prefix associated with
        the namespace in a containing schema.  This value, if present,
        is used as a prefix to allow a deeper module hierarchy."""
        return self.__modulePrefix
    def setModulePrefix (self, module_prefix):
        self.__modulePrefix = module_prefix
        return self
    __modulePrefix = None

    def namespaceModuleMap (self):
        """A map from namespace URIs to the module to be used for the
        corresponding generated binding.

        Module values are adjusted by L{modulePrefix} if that has been
        specified.

        An entry in this map for a namespace supersedes the module
        specified in moduleList if the namespace is defined by an
        entrypoint schema.

        @return: A reference to the namespace module map.
        """
        return self.__namespaceModuleMap
    __namespaceModuleMap = None

    def archivePath (self):
        """A colon-separated list of paths from which namespace
        archives can be read.

        The default path is the contents of the C{PYXB_ARCHIVE_PATH}
        environment variable, or the standard path configured at
        installation time.  Any file with the extension C{.wxs} found
        in one of these directories is examined to see whether it is a
        namespace archive.
        """
        return self.__archivePath
    def setArchivePath (self, archive_path):
        self.__archivePath = archive_path
        return self
    __archivePath = None

    def noLoadNamespaces (self):
        """A frozenset of namespaces that must not be loaded from an archive."""
        return frozenset(self.__noLoadNamespaces)
    def _setNoLoadNamespaces (self, namespace_set):
        """Record the set of namespaces that should not be loaded from an archive.

        The expectation is that any required entities in the namespace
        will be defined by loading schema."""
        self.__noLoadNamespaces.clear()
        self.__noLoadNamespaces.update([ pyxb.namespace.NamespaceInstance(_ns) for _ns in namespace_set ])
    def addNoLoadNamespace (self, namespace):
        """Mark that the specified namespace should not be loaded from an archive.

        Use this when you are generating bindings for an application
        that has a restricted profile of a namespace that would
        otherwise be read from an archive.  Be aware that this removes
        any knowledge of any archive in which this namespace is
        present as a non-private member."""
        self.__noLoadNamespaces.add(pyxb.namespace.NamespaceInstance(namespace))
    __noloadNamespaces = None

    def importAugmentableNamespaces (self):
        """A list of namespaces for which new bindings are allowd."""
        return frozenset(self.__importAugmentableNamespaces)
    def _setImportAugmentableNamespaces (self, namespace_set):
        """Return the set of namespaces that may be augmented by import directives."""
        self.__importAugmentableNamespaces.clear()
        self.__importAugmentableNamespaces.update([ pyxb.namespace.NamespaceInstance(_ns) for _ns in namespace_set ])
    def addImportAugmentableNamespace (self, namespace):
        """Mark that the specified namespace may be imported by new bindings.

        Normally namespaces that are available from archives are
        considered to be complete, and schema locations in import
        directives are ignored.  Use this to indicate that the
        bindings being generated import new bindings.

        Note that attempts to import schema that contributed to the
        archive will only be detected if the archive was generated
        from the same schemaLocation URI; if the archive was generated
        from a different source component definitions might
        conflict."""
        self.__importAugmentableNamespaces.add(pyxb.namespace.NamespaceInstance(namespace))
    __importAugmentableNamespaces = None

    def archiveToFile (self):
        """Optional file into which the archive of namespaces will be written.

        Subsequent generation actions can read pre-parsed namespaces
        from this file, and therefore reference the bindings that were
        built earlier rather than re-generating them.

        The file name should normally end with C{.wxs}."""
        return self.__archiveToFile
    def setArchiveToFile (self, archive_to_file):
        self.__archiveToFile = archive_to_file
        return self
    __archiveToFile = None

    def setNamespaceVisibility (self, namespace, visibility):
        namespace = pyxb.namespace.NamespaceInstance(namespace)
        self.__namespaceVisibilityMap[namespace] = visibility
        pass
    def _setNamespaceVisibilities (self, public, private):
        if public is None:
            public = set()
        if private is None:
            private = set()
        self.__namespaceVisibilityMap.clear()
        self.__namespaceVisibilityMap.update(dict.fromkeys(public, True))
        self.__namespaceVisibilityMap.update(dict.fromkeys(private, False))
    def namespaceVisibilityMap (self):
        """Indicates, for specific namespaces, whether their
        visibility in the archive should be public or private."""
        return self.__namespaceVisibilityMap.copy()
    __namespaceVisibilityMap = None

    def defaultNamespacePublic (self):
        """Indicates whether unmentioned namespaces will be public or private (default) in the archive.

        A namespace is I{mentioned} if it is the target namespace of
        an entrypoint schema, or appears in a namespace visibility
        specification.  I.e., this default applies only to namespaces
        that are modified as a result of including some schema, which
        is generally a local customization of something.
        """
        return self.__defaultNamespacePublic
    def setDefaultNamespacePublic (self, default_namespace_public):
        self.__defaultNamespacePublic = default_namespace_public
    __defaultNamespacePublic = None

    def validateChanges (self):
        """Indicates whether the bindings should validate mutations
        against the content model."""
        return self.__validateChanges
    def setValidateChanges (self, validate_changes):
        self.__validateChanges = validate_changes
        return self
    __validateChanges = None

    def writeForCustomization (self):
        """Indicates whether the binding Python code should be written into a sub-module for customization.

        If enabled, a module C{path.to.namespace} will be written to
        the file C{path/to/raw/namespace.py}, so that the file
        C{path/to/namespace.py} can import it and override behavior."""
        return self.__writeForCustomization
    def setWriteForCustomization (self, write_for_customization):
        self.__writeForCustomization = write_for_customization
        return self
    __writeForCustomization = None

    def allowAbsentModule (self):
        """Indicates whether the code generator is permitted to
        process namespace for which no module path can be determined.

        Use this only when generating bindings that will not be
        referenced by other bindings."""
        return self.__allowAbsentModule
    def setAllowAbsentModule (self, allow_absent_module):
        self.__allowAbsentModule = allow_absent_module
        return self
    __allowAbsentModule = None

    def allowBuiltinGeneration (self):
        """Indicates whether bindings will be written for namespaces that are built-in to PyXB.

        This must be enabled when building bindings for the XML,
        XMLSchema instance, and other built-in namespaces.  Normally
        generation of these namespaces is inhibited lest it produce
        inconsistencies."""
        return self.__allowBuiltinGeneration
    def setAllowBuiltinGeneration (self, allow_builtin_generation):
        self.__allowBuiltinGeneration = allow_builtin_generation
        return self
    __allowBuiltinGeneration = None

    def uriContentArchiveDirectory (self):
        """The directory path into which any content retrieved by URI will be written.

        This serves as a local cache, and to give you an opportunity
        to inspect material retrieved from some other system.
        @rtype: C{str}"""
        return self.__uriContentArchiveDirectory
    def setUriContentArchiveDirectory (self, ucad):
        self.__uriContentArchiveDirectory = ucad
    __uriContentArchiveDirectory = None

    def loggingConfigFile (self):
        """A file provided to L{logging.config.fileConfig} to control log messages.

        In the absence of other configuration the Python standard logging infrastructure is used in its
        default configuration.

        @rtype: C{str}"""
        return self.__loggingConfigFile
    def setLoggingConfigFile (self, logging_config_file):
        self.__loggingConfigFile = logging_config_file
    __loggingConfigFile = None

    def __init__ (self, *args, **kw):
        """Create a configuration to be used for generating bindings.

        Arguments are treated as additions to the schema location list
        after all keywords have been processed.

        @keyword binding_root: Invokes L{setBindingRoot}
        @keyword schema_root: Invokes L{setSchemaRoot}
        @keyword schema_stripped_prefix: Invokes L{setSchemaStrippedPrefix}
        @keyword location_prefix_rewrite_map: Invokes L{setLocationPrefixRewriteMap}
        @keyword schema_location_list: Invokes L{setSchemaLocationList}
        @keyword module_list: Invokes L{_setModuleList}
        @keyword module_prefix: Invokes L{setModulePrefix}
        @keyword archive_path: Invokes L{setArchivePath}
        @keyword no_load_namespaces: Invokes L{_setNoLoadNamespaces}
        @keyword import_augmentable_namespaces: Invokes L{_setImportAugmentableNamespaces}
        @keyword archive_to_file: Invokes L{setArchiveToFile}
        @keyword public_namespace: Invokes L{setNamespaceVisibility}
        @keyword private_namespace: Invokes L{setNamespaceVisibility}
        @keyword default_namespace_public: Invokes L{setDefaultNamespacePublic}
        @keyword validate_changes: Invokes L{setValidateChanges}
        @keyword namespace_module_map: Initializes L{namespaceModuleMap}
        @keyword schemas: Invokes L{setSchemas}
        @keyword namespaces: Invokes L{setNamespaces}
        @keyword write_for_customization: Invokes L{setWriteForCustomization}
        @keyword allow_builtin_generation: Invokes L{setAllowBuiltinGeneration}
        @keyword allow_absent_module: Invokes L{setAllowAbsentModule}
        @keyword generate_to_files: Sets L{generateToFiles}
        @keyword uri_content_archive_directory: Invokes L{setUriContentArchiveDirectory}
        @keyword logging_config_file: Invokes L{setLoggingConfigFile}
        """
        argv = kw.get('argv')
        if argv is not None:
            kw = {}
        self.__bindingRoot = kw.get('binding_root', self._DEFAULT_bindingRoot)
        self.__schemaRoot = kw.get('schema_root', os.getcwd() + os.path.sep)
        self.__schemaStrippedPrefix = kw.get('schema_stripped_prefix')
        self.__locationPrefixRewriteMap = kw.get('location_prefix_rewrite_map', {})
        self.__schemas = []
        self.__schemaLocationList = kw.get('schema_location_list', [])[:]
        self.__moduleList = kw.get('module_list', [])[:]
        self.__modulePrefix = kw.get('module_prefix')
        self.__archivePath = kw.get('archive_path', pyxb.namespace.archive.GetArchivePath())
        self.__noLoadNamespaces = kw.get('no_load_namespaces', set()).copy()
        self.__importAugmentableNamespaces = kw.get('import_augmentable_namespaces', set()).copy()
        self.__archiveToFile = kw.get('archive_to_file')
        self.__namespaceVisibilityMap = {}
        self._setNamespaceVisibilities(kw.get('public_namespaces', set()), kw.get('private_namespaces', set()))
        self.__defaultNamespacePublic = kw.get('default_namespace_public', False)
        self.__validateChanges = kw.get('validate_changes', True)
        self.__namespaceModuleMap = kw.get('namespace_module_map', {}).copy()
        self.__schemas = kw.get('schemas', [])[:]
        self.__namespaces = set(kw.get('namespaces', []))
        self.__writeForCustomization = kw.get('write_for_customization', False)
        self.__allowBuiltinGeneration = kw.get('allow_builtin_generation', False)
        self.__allowAbsentModule = kw.get('allow_absent_module', False)
        self.__generateToFiles = kw.get('generate_to_files', True)
        self.__uriContentArchiveDirectory = kw.get('uri_content_archive_directory')
        self.__loggingConfigFile = kw.get('logging_config_file')
        self.__unnamedModulePaths = set()

        if argv is not None:
            self.applyOptionValues(*self.optionParser().parse_args(argv))
        [ self.addSchemaLocation(_a) for _a in args ]

        self.__generationUID = pyxb.utils.utility.UniqueIdentifier()

        pyxb.namespace.XML.validateComponentModel()

    __stripSpaces_re = re.compile('\s\s\s+')
    def __stripSpaces (self, string):
        return self.__stripSpaces_re.sub(' ', string)

    __OptionSetters = (
        ('binding_root', setBindingRoot),
        ('schema_root', setSchemaRoot),
        ('schema_stripped_prefix', setSchemaStrippedPrefix),
        ('location_prefix_rewrite', argAddLocationPrefixRewrite),
        ('schema_location', setSchemaLocationList),
        ('module', _setModuleList),
        ('module_prefix', setModulePrefix),
        ('archive_path', setArchivePath),
        ('no_load_namespace', _setNoLoadNamespaces),
        ('import_augmentable_namespace', _setImportAugmentableNamespaces),
        ('archive_to_file', setArchiveToFile),
        ('default_namespace_public', setDefaultNamespacePublic),
        ('validate_changes', setValidateChanges),
        ('write_for_customization', setWriteForCustomization),
        ('allow_builtin_generation', setAllowBuiltinGeneration),
        ('allow_absent_module', setAllowAbsentModule),
        ('uri_content_archive_directory', setUriContentArchiveDirectory),
        ('logging_config_file', setLoggingConfigFile)
        )
    def applyOptionValues (self, options, args=None):
        for (tag, method) in self.__OptionSetters:
            v = getattr(options, tag)
            if v is not None:
                method(self, v)
        public_namespaces = getattr(options, 'public_namespace')
        private_namespaces = getattr(options, 'private_namespace')
        self._setNamespaceVisibilities(public_namespaces, private_namespaces)
        if args is not None:
            self.__schemaLocationList.extend(args)
        pyxb.utils.utility.SetLocationPrefixRewriteMap(self.locationPrefixRewriteMap())
        if self.__loggingConfigFile is not None:
            logging.config.fileConfig(self.__loggingConfigFile)

    def setFromCommandLine (self, argv=None):
        if argv is None:
            argv = sys.argv[1:]
        (options, args) = self.optionParser().parse_args(argv)
        self.applyOptionValues(options, args)
        return self

    def generationUID (self):
        """A unique identifier associated with this Generator instance.

        This is an instance of L{pyxb.utils.utility.UniqueIdentifier}.
        Its associated objects are
        L{pyxb.namespace.archive._SchemaOrigin} instances, which
        identify schema that contribute to the definition of a
        namespace."""
        return self.__generationUID
    __generationUID = None

    def optionParser (self, reset=False):
        """Return an C{optparse.OptionParser} instance tied to this configuration.

        @param reset: If C{False} (default), a parser created in a
        previous invocation will be returned.  If C{True}, any
        previous option parser is discarded and a new one created.
        @type reset: C{bool}
        """
        if reset or (self.__optionParser is None):
            parser = optparse.OptionParser(usage="%prog [options] [more schema locations...]",
                                           version='%%prog from PyXB %s' % (pyxb.__version__,),
                                           description='Generate bindings from a set of XML schemas')

            group = optparse.OptionGroup(parser, 'Identifying Schema', 'Specify and locate schema for which bindings should be generated.')
            group.add_option('--schema-location', '-u', metavar="FILE_or_URL",
                             action='append',
                             help=self.__stripSpaces(self.argAddSchemaLocation.__doc__))
            group.add_option('--schema-root', metavar="DIRECTORY",
                             help=self.__stripSpaces(self.schemaRoot.__doc__))
            group.add_option('--schema-stripped-prefix', metavar="TEXT", type='string',
                             help=self.__stripSpaces(self.schemaStrippedPrefix.__doc__))
            group.add_option('--location-prefix-rewrite', metavar="TEXT", type='string',
                             help=self.__stripSpaces(self.argAddLocationPrefixRewrite.__doc__))
            group.add_option('--uri-content-archive-directory', metavar="DIRECTORY",
                             help=self.__stripSpaces(self.uriContentArchiveDirectory.__doc__))
            parser.add_option_group(group)

            group = optparse.OptionGroup(parser, 'Configuring Bindings', 'Specify where generated bindings should be written, and how they will be accessed from Python.')
            group.add_option('--module', '-m', metavar="MODULE",
                             action='append',
                             help=self.__stripSpaces(self.addModuleName.__doc__))
            group.add_option('--module-prefix', metavar="MODULE",
                             help=self.__stripSpaces(self.modulePrefix.__doc__))
            group.add_option('--binding-root', metavar="DIRECTORY",
                             help=self.__stripSpaces(self.bindingRoot.__doc__))
            group.add_option('-r', '--write-for-customization',
                             action='store_true', dest='write_for_customization',
                             help=self.__stripSpaces(self.writeForCustomization.__doc__ + ' This option turns on the feature.'))
            group.add_option('--no-write-for-customization',
                             action='store_false', dest='write_for_customization',
                             help=self.__stripSpaces(self.writeForCustomization.__doc__ + ' This option turns off the feature (I{default}).'))
            parser.add_option_group(group)

            group = optparse.OptionGroup(parser, 'Reading Namespace Archives', 'Locating and loading (or inhibiting load of) namespace archives.')
            group.add_option('--archive-path', metavar="PATH",
                             help=self.__stripSpaces(self.archivePath.__doc__))
            group.add_option('--import-augmentable-namespace', metavar="URI",
                             action='append',
                             help=self.__stripSpaces(self.addImportAugmentableNamespace.__doc__))
            group.add_option('--no-load-namespace', metavar="URI",
                             action='append',
                             help=self.__stripSpaces(self.addNoLoadNamespace.__doc__))
            parser.add_option_group(group)

            group = optparse.OptionGroup(parser, 'Writing Namespace Archives', 'Control the location and content of a namespace archive corresponding to a binding generation.')
            group.add_option('--archive-to-file', metavar="FILE",
                             help=self.__stripSpaces(self.archiveToFile.__doc__))
            group.add_option('--public-namespace', metavar="URI",
                             action='append',
                             help=self.__stripSpaces(self.namespaceVisibilityMap.__doc__ + ' This option adds the namespace as a public archive member.'))
            group.add_option('--private-namespace', metavar="URI",
                             action='append',
                             help=self.__stripSpaces(self.namespaceVisibilityMap.__doc__ + ' This option adds the namespace as a private archive member.'))
            group.add_option('--default-namespace-public',
                             action="store_true", dest='default_namespace_public',
                             help=self.__stripSpaces(self.defaultNamespacePublic.__doc__ + ' This option makes the default C{public} (I{default}).'))
            group.add_option('--default-namespace-private',
                             action="store_false", dest='default_namespace_public',
                             help=self.__stripSpaces(self.defaultNamespacePublic.__doc__ + ' This option makes the default C{private}.'))
            parser.add_option_group(group)

            group = optparse.OptionGroup(parser, 'Configuring Binding Code Generation', "Control the style and content of the generated bindings.  This is not well-supported, and you are advised to pretend these options don't exist.")
            group.add_option('--validate-changes',
                              action='store_true', dest='validate_changes',
                              help=self.__stripSpaces(self.validateChanges.__doc__ + ' This option turns on validation (default).'))
            group.add_option('--no-validate-changes',
                              action='store_false', dest='validate_changes',
                              help=self.__stripSpaces(self.validateChanges.__doc__ + ' This option turns off validation.'))
            parser.add_option_group(group)

            group = optparse.OptionGroup(parser, 'Miscellaneous Options', "Anything else.")
            group.add_option('--logging-config-file', metavar="FILE",
                             help=self.__stripSpaces(self.loggingConfigFile.__doc__))
            parser.add_option_group(group)

            group = optparse.OptionGroup(parser, 'Maintainer Options', "Don't use these.  They don't exist.  If they did, they'd do different things at different times, and if you used them you'd probably be sorry.")

            group.add_option('--allow-absent-module',
                              action='store_true', dest='allow_absent_module',
                              help=self.__stripSpaces(self.allowAbsentModule.__doc__ + ' This option turns on the feature.'))
            group.add_option('--no-allow-absent-module',
                             action='store_false', dest='allow_absent_module',
                             help=self.__stripSpaces(self.allowAbsentModule.__doc__ + ' This option turns off the feature (default).'))
            group.add_option('--allow-builtin-generation',
                             action='store_true', dest='allow_builtin_generation',
                             help=self.__stripSpaces(self.allowBuiltinGeneration.__doc__ + ' This option turns on the feature.'))
            group.add_option('--no-allow-builtin-generation',
                             action='store_false', dest='allow_builtin_generation',
                             help=self.__stripSpaces(self.allowBuiltinGeneration.__doc__ + ' This option turns off the feature (default).'))
            parser.add_option_group(group)

            self.__optionParser = parser
        return self.__optionParser
    __optionParser = None

    def getCommandLineArgs (self):
        """Return a command line option sequence that could be used to
        construct an equivalent configuration.

        @note: If you extend the option parser, as is done by
        C{pyxbgen}, this may not be able to reconstruct the correct
        command line."""
        opts = []
        module_list = self.moduleList()
        schema_list = self.schemaLocationList()
        while module_list and schema_list:
            ml = module_list.pop(0)
            sl = schema_list.pop(0)
            if isinstance(sl, tuple):
                sl = sl[0]
            opts.extend(['--schema-location=' + sl, '--module=' + ml])
        for sl in schema_list:
            opts.append('--schema-location=' + sl)
        if self.schemaRoot() is not None:
            opts.append('--schema-root=' + self.schemaRoot())
        if self.schemaStrippedPrefix() is not None:
            opts.append('--schema-stripped-prefix=%s' + self.schemaStrippedPrefix())
        for (pfx, sub) in self.locationPrefixRewriteMap():
            opts.append('--location-prefix-rewrite=%s=%s' % (pfx, sub))
        if self.modulePrefix() is not None:
            opts.append('--module-prefix=' + self.modulePrefix())
        opts.append('--binding-root=' + self.bindingRoot())
        if self.archivePath() is not None:
            opts.append('--archive-path=' + self.archivePath())
        for ns in self.noLoadNamespaces():
            opts.append('--no-load-namespace=' + ns.uri())
        for ns in self.importAugmentableNamespaces():
            opts.append('--import-augmentable-namespace=' + ns.uri())
        if self.archiveToFile() is not None:
            opts.append('--archive-to-file=' + self.archiveToFile())
        for (ns, visibility) in self.namespaceVisibilityMap():
            if visibility:
                opts.append('--public-namespace=' + ns.uri())
            else:
                opts.append('--private-namespace=' + ns.uri())
        if self.defaultNamespacePublic():
            opts.append('--default-namespace-public')
        else:
            opts.append('--default-namespace-private')
        for (val, opt) in ( (self.validateChanges(), 'validate-changes'),
                            (self.writeForCustomization(), 'write-for-customization'),
                            (self.allowAbsentModule(), 'allow-absent-module'),
                            (self.allowBuiltinGeneration(), 'allow-builtin-generation') ):
            if val:
                opts.append('--' + opt)
            else:
                opts.append('--no-' + opt)
        if self.uriContentArchiveDirectory() is not None:
            opts.append('--uri-content-archive-directory=%s' + self.uriContentArchiveDirectory())
        return opts

    def normalizeSchemaLocation (self, sl):
        ssp = self.schemaStrippedPrefix()
        if ssp and sl.startswith(ssp):
            sl = sl[len(ssp):]
        return pyxb.utils.utility.NormalizeLocation(sl, self.schemaRoot())

    def assignModulePath (self, module_record, module_path=None):
        """Provide a Python module path for the module record.

        This is the path by which the module bindings associated with
        C{module_record} will be imported.

        If a path had already been assigned to the module, it is left
        in place.

        @param module_record: Information about a collection of related bindings
        @type module_record: L{pyxb.namespace.archive.ModuleRecord}

        @param module_path: Default path to use
        @type module_path: C{str}

        @return: C{module_record}
        """
        if module_record.modulePath() is not None:
            return module_record
        namespace = module_record.namespace()
        if not namespace.isAbsentNamespace():
            # Use the namespace prefix from a referencing schema if no other clue was given
            if (module_path is None) and not (namespace.prefix() is None):
                module_path = namespace.prefix()
            # Prefer an existing assignment over a new one
            module_path = self.namespaceModuleMap().get(namespace.uri(), module_path)
        if (module_path is None) and self.generateToFiles():
            module_path = pyxb.utils.utility.MakeUnique('binding', self.__unnamedModulePaths)
        if (module_path is not None) and self.modulePrefix(): # non-empty value
            # Prepend a configured module prefix
            module_path = '.'.join([self.modulePrefix(), module_path])
        module_record.setModulePath(module_path)
        return module_record

    __didResolveExternalSchema = False
    def resolveExternalSchema (self):
        if self.__didResolveExternalSchema:
            return

        # Locate all relevant archives and the namespaces they
        # provide.
        pyxb.namespace.archive.NamespaceArchive.PreLoadArchives(self.archivePath())

        # Mark the namespaces we were told not to load.  These may be
        # namespaces for which we already have bindings in the search
        # path, but we want to generate completely new ones.
        for ns in self.noLoadNamespaces():
            assert isinstance(ns, pyxb.namespace.Namespace)
            _log.info("Namespace %s marked not loadable" % (ns,))
            ns.markNotLoadable()

        # Mark the namespaces that we permit to be extended by import
        # statements.
        for ns in self.importAugmentableNamespaces():
            assert isinstance(ns, pyxb.namespace.Namespace)
            _log.info("Namespace %s marked import-augmentable" % (ns,))
            ns.setImportAugmentable(True)

        # Read all the schema we were told about.
        while self.__schemaLocationList:
            sl = self.__schemaLocationList.pop(0)
            if isinstance(sl, tuple):
                (sl, converter) = sl
            else:
                converter = None
            try:
                if converter is None:
                    schema = xs.schema.CreateFromLocation(absolute_schema_location=self.normalizeSchemaLocation(sl),
                                                          generation_uid=self.generationUID(),
                                                          uri_content_archive_directory=self.uriContentArchiveDirectory())
                else:
                    schema = converter(self, sl)
                self.addSchema(schema)
            except pyxb.SchemaUniquenessError as e:
                _log.info('Skipped redundant translation of %s defining %s', e.schemaLocation(), e.namespace())
                self.addSchema(e.existingSchema())

        # Assign Python modules to hold bindings for the schema we're
        # processing.
        for schema in self.__schemas:
            if isinstance(schema, six.string_types):
                schema = xs.schema.CreateFromDocument(schema, generation_uid=self.generationUID())
            origin = schema.originRecord()
            assert origin is not None
            module_path = None
            if self.__moduleList:
                module_path = self.__moduleList.pop(0)
            self.assignModulePath(origin.moduleRecord(), module_path)
            assert schema.targetNamespace() == origin.moduleRecord().namespace()
            self.addNamespace(schema.targetNamespace())
        self.__didResolveExternalSchema = True

        # Discard any existing component information
        self.__componentGraph = None
        self.__componentOrder = None

    def __graphFromComponents (self, components, include_lax):
        components = components.copy()
        component_graph = pyxb.utils.utility.Graph()
        need_visit = components.copy()
        bindable_fn = lambda _c: isinstance(_c, xs.structures.ElementDeclaration) or _c.isTypeDefinition()
        while 0 < len(need_visit):
            c = need_visit.pop()
            assert c is not None
            assert bindable_fn(c) or include_lax
            assert c._objectOrigin() is not None, '%s %s has no origin' % (type(c), c)
            component_graph.addNode(c)
            br = c.bindingRequires(reset=True, include_lax=include_lax)
            for cd in br:
                assert bindable_fn(cd) or include_lax, '%s produced %s in requires' % (type(c), type(cd))
                if cd._objectOrigin() is None:
                    assert isinstance(cd, (pyxb.xmlschema.structures.Annotation, pyxb.xmlschema.structures.Wildcard))
                    continue
                if (cd._objectOrigin().moduleRecord() in self.__moduleRecords) and not (cd in components):
                    components.add(cd)
                    need_visit.add(cd)
                if cd in components:
                    component_graph.addEdge(c, cd)
        return component_graph

    def __resolveComponentDependencies (self):
        self.resolveExternalSchema()

        bindable_fn = lambda _c: isinstance(_c, xs.structures.ElementDeclaration) or _c.isTypeDefinition()

        self.__moduleRecords = set()
        all_components = set()
        for origin in self.generationUID().associatedObjects():
            mr = origin.moduleRecord()
            if not (mr in self.__moduleRecords):
                self.__moduleRecords.add(mr)
                mr.completeGenerationAssociations()
            all_components.update(origin.originatedObjects())

        namespaces = set()
        for mr in self.__moduleRecords:
            if mr.namespace().isBuiltinNamespace() and not self.allowBuiltinGeneration():
                continue
            namespaces.add(mr.namespace())
        pyxb.namespace.resolution.ResolveSiblingNamespaces(namespaces)

        # Mark module visibility.  Entry-point namespaces default to
        # public.
        for ns in self.namespaces():
            self.__namespaceVisibilityMap.setdefault(ns, True)

        # Generate the graph from all components and descend into lax
        # requirements; otherwise we might miss anonymous types hidden
        # inside attribute declarations and the like.
        component_graph = self.__graphFromComponents(all_components, True)

        binding_components = set(filter(bindable_fn, component_graph.nodes()))
        for c in binding_components:
            assert bindable_fn(c), 'Unexpected %s in binding components' % (type(c),)
            c._setBindingNamespace(c._objectOrigin().moduleRecord().namespace())

        component_order = []
        root_sets = self.__graphFromComponents(binding_components, False).rootSetOrder()
        if root_sets is None:
            raise pyxb.BindingGenerationError('Unable to partial-order named components')
        for rs in root_sets:
            component_order.extend(sorted(rs, key=lambda _c: _c.schemaOrderSortKey()))

        self.__componentGraph = component_graph
        self.__componentOrder = component_order

    __moduleRecords = None
    __componentGraph = None
    __componentOrder = None

    def moduleRecords (self):
        """The set of L{pyxb.namespace.archive.ModuleRecord} instances
        associated with schema processed in this generation
        instance.

        These should be in one-to-one correspondence with the
        namespaces for which bindings are being generated.  Multiple
        input schemas may contribute to a single module record; all
        material in that record is placed in a single binding file.
        """
        if self.__moduleRecords is None:
            self.__resolveComponentDependencies()
        return self.__moduleRecords

    def componentGraph (self):
        if self.__componentGraph is None:
            self.__resolveComponentDependencies()
        return self.__componentGraph

    def componentOrder (self):
        if self.__componentOrder is None:
            self.__resolveComponentDependencies()
        return self.__componentOrder

    def __generateBindings (self):

        # Note that module graph may have fewer nodes than
        # self.moduleRecords(), if a module has no components that
        # require binding generation.

        module_graph = pyxb.utils.utility.Graph()
        [ module_graph.addRoot(_mr) for _mr in self.moduleRecords() ]
        for (s, t) in self.componentGraph().edges():
            module_graph.addEdge(s._objectOrigin().moduleRecord(), t._objectOrigin().moduleRecord())
        module_scc_order = module_graph.sccOrder()

        record_binding_map = {}
        modules = []
        nsvm = self.namespaceVisibilityMap()
        for mr_scc in module_scc_order:
            scc_modules = [ ]
            for mr in mr_scc:
                mr._setIsPublic(nsvm.get(mr.namespace(), self.defaultNamespacePublic()))
                self.assignModulePath(mr)
                if (mr.modulePath() is None) and self.generateToFiles():
                    raise pyxb.BindingGenerationError('No prefix or module name available for %s' % (mr,))
                if (not mr.isPublic()) and (mr.modulePath() is not None):
                    elts = mr.modulePath().split('.')
                    elts[-1] = '_%s' % (elts[-1],)
                    mr.setModulePath('.'.join(elts))
                nsm = NamespaceModule(self, mr, mr_scc)
                record_binding_map[mr] = nsm
                scc_modules.append(nsm)

            scc_modules.sort(key=lambda _nm: _nm.namespace().uri())
            modules.extend(scc_modules)
            if 1 < len(mr_scc):
                ngm = NamespaceGroupModule(self, scc_modules)
                modules.append(ngm)
                for nsm in scc_modules:
                    nsm.setNamespaceGroupModule(ngm)

        element_declarations = []
        type_definitions = []
        for c in self.componentOrder():
            if isinstance(c, xs.structures.ElementDeclaration) and c._scopeIsGlobal():
                # Only bind elements this pass, so their names get priority in deconfliction
                nsm = record_binding_map[c._objectOrigin().moduleRecord()]
                nsm.bindComponent(c)
                element_declarations.append(c)
            elif c.isTypeDefinition():
                type_definitions.append(c)
            else:
                # No binding generation required
                pass

        simple_type_definitions = []
        complex_type_definitions = []
        for td in type_definitions:
            nsm = record_binding_map[td._objectOrigin().moduleRecord()]
            assert nsm is not None, 'No namespace module for %s type %s scope %s namespace %s' % (td.expandedName(), type(td), td._scope(), td.bindingNamespace)
            module_context = nsm.bindComponent(td)
            assert isinstance(module_context, _ModuleNaming_mixin), 'Unexpected type %s' % (type(module_context),)
            if isinstance(td, xs.structures.SimpleTypeDefinition):
                _PrepareSimpleTypeDefinition(td, self, nsm, module_context)
                simple_type_definitions.append(td)
            elif isinstance(td, xs.structures.ComplexTypeDefinition):
                _PrepareComplexTypeDefinition(td, self, nsm, module_context)
                complex_type_definitions.append(td)
            else:
                assert False, 'Unexpected component type %s' % (type(td),)

        for ngm in modules:
            if isinstance(ngm, NamespaceGroupModule):
                for m in ngm.namespaceModules():
                    m.addImportsFrom(ngm)

        for std in simple_type_definitions:
            GenerateSTD(std, self)
        for ctd in complex_type_definitions:
            GenerateCTD(ctd, self)
        for ed in element_declarations:
            GenerateED(ed, self)

        self.__bindingModules = modules

    __bindingModules = None
    def bindingModules (self):
        if self.__componentGraph is None:
            self.__resolveComponentDependencies()
        if self.__bindingModules is None:
            self.__generateBindings()
        return self.__bindingModules

    def writeNamespaceArchive (self):
        archive_file = self.archiveToFile()
        if archive_file is not None:
            ns_archive = pyxb.namespace.archive.NamespaceArchive(generation_uid=self.generationUID())
            try:
                ns_archive.writeNamespaces(pyxb.utils.utility.OpenOrCreate(archive_file))
                _log.info('Saved parsed schema to %s URI', archive_file)
            except Exception as e:
                _log.exception('Failure saving preprocessed schema to %s', archive_file)
                #try:
                #    os.unlink(component_model_file)
                #except (OSError, IOError), e:
                #    pass
                if isinstance(e, (AssertionError, AttributeError, TypeError)):
                    raise

    def moduleForComponent (self, component):
        return _ModuleNaming_mixin.ComponentBindingModule(component)
