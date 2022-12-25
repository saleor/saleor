# -*- coding: utf-8 -*-
# Copyright 2012, Peter A. Bigot
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

"""This module provides Finite Automata with Counters.

FACs are type of state machine where a transition may include a
constraint and a modification to a set of counters.  They are used to
implement regular expressions with numerical constraints, as are found
in POSIX regexp, Perl, and XML schema.

The implementation here derives from U{Regular Expressions with
Numerical Constraints and Automata with Counters
<https://bora.uib.no/bitstream/1956/3628/3/Hovland_LNCS%205684.pdf>},
Dag Hovland, Lecture Notes in Computer Science, 2009, Volume 5684,
Theoretical Aspects of Computing - ICTAC 2009, Pages 231-245.  In what
follows, this reference will be denoted B{HOV09}.

A regular expression is directly translated into a term tree, where
nodes are operators such as sequence, choice, and counter
restrictions, and the leaf nodes denote symbols in the language of the
regular expression.

In the case of XML content models, the symbols include L{element
declarations <pyxb.xmlschema.structures.ElementDeclaration>} and
L{wildcard elements <pyxb.xmlschema.structures.Wildcard>}.  A
numerical constraint node corresponds to an L{XML particle
<pyxb.xmlschema.structures.Particle>}, and choice and sequence nodes
derive from L{model groups <pyxb.xmlschema.structures.ModelGroup>} of
types B{choice} and B{sequence}.  As suggested in U{The Membership
Problem for Regular Expressions with Unordered Concatenation and
Numerical Constraints <http://www.ii.uib.no/~dagh/presLATA2012.pdf>}
the B{all} content model can be translated into state machine using
choice and sequence at the cost of a quadratic size explosion.  Since
some XML content models might have a hundred terms in an unordered
catenation, this is not acceptable, and the implementation here
optimizes this construct by creating a leaf node in the automaton
which in turn contains sub-automata for each term, and permits an exit
transition only when all the terms that are required have been
completed.

@note: In XSD 1.1 the restriction that terms in an B{all} model group
occur at most once has been removed.  Since the current implementation
removes a completed term from the set of available terms, this will
not work: instead the subconfiguration with its counter values must be
retained between matches.
"""

import operator
import functools
import logging
from pyxb.utils import six
from pyxb.utils.six.moves import xrange

log_ = logging.getLogger(__name__)

class FACError (Exception):
    pass

class InvalidTermTreeError (FACError):
    """Exception raised when a FAC term tree is not a tree.

    For example, a L{Symbol} node appears multiple times, or a cycle is detected."""

    parent = None
    """The L{MultiTermNode} containing the term that proves invalidity"""

    term = None
    """The L{Node} that proves invalidity"""

    def __init__ (self, *args):
        (self.parent, self.term) = args
        super(InvalidTermTreeError, self).__init__(*args)

class UpdateApplicationError (FACError):
    """Exception raised when an unsatisfied update instruction is executed.

    This indicates an internal error in the implementation."""

    update_instruction = None
    """The L{UpdateInstruction} with an unsatisfied L{CounterCondition}"""

    values = None
    """The unsatisfying value map from L{CounterCondition} instances to integers"""

    def __init__ (self, *args):
        (self.update_instruction, self.values) = args
        super(UpdateApplicationError, self).__init__(*args)

class AutomatonStepError (Exception):
    """Symbol rejected by L{Configuration_ABC.step}.

    The exception indicates that the proposed symbol either failed to
    produce a transition (L{UnrecognizedSymbolError}) or produced
    multiple equally valid transitions
    (L{NondeterministicSymbolError})."""

    configuration = None
    """The instance of L{Configuration_ABC} that raised the exception.
    From L{Configuration_ABC.acceptableSymbols} you can determine what
    alternatives might be present."""

    symbol = None
    """The symbol that was not accepted."""

    def __get_acceptable (self):
        """A list of symbols that the configuration would accept in its current state."""
        return self.configuration.acceptableSymbols()
    acceptable = property(__get_acceptable)

    def __init__ (self, *args):
        (self.configuration, self.symbol) = args
        super(AutomatonStepError, self).__init__(*args)

class UnrecognizedSymbolError (AutomatonStepError):
    """L{Configuration.step} failed to find a valid transition."""
    pass

class NondeterministicSymbolError (AutomatonStepError):
    """L{Configuration.step} found multiple transitions."""
    pass

class SymbolMatch_mixin (object):
    """Mix-in used by symbols to provide a custom match implementation.

    If a L{State.symbol} value is an instance of this mix-in, then it
    will be used to validate a candidate symbol for a match."""

    def match (self, symbol):
        raise NotImplementedError('%s.match' % (type(self).__name__,))

class State (object):
    """A thin wrapper around an object reference.

    The state of the automaton corresponds to a position, or marked
    symbol, in the term tree.  Because the same symbol may appear at
    multiple locations in the tree, and the distinction between these
    positions is critical, a L{State} wrapper is provided to maintain
    distinct values."""

    def __init__ (self, symbol, is_initial, final_update=None, is_unordered_catenation=False):
        """Create a FAC state.

        @param symbol: The symbol associated with the state.
        Normally initialized from the L{Symbol.metadata} value.  The
        state may be entered if, among other conditions, the L{match}
        routine accepts the proposed input as being consistent with
        this value.

        @param is_initial: C{True} iff this state may serve as the
        first state of the automaton.

        @param final_update: C{None} if this state is not an
        accepting state of the automaton; otherwise a set of
        L{UpdateInstruction} values that must be satisfied by the
        counter values in a configuration as a further restriction of
        acceptance.

        @param is_unordered_catenation: C{True} if this state has
        subautomata that must be matched to execute the unordered
        catenation of an L{All} node; C{False} if this is a regular
        symbol."""
        self.__symbol = symbol
        self.__isInitial = not not is_initial
        self.__finalUpdate = final_update
        self.__isUnorderedCatenation = is_unordered_catenation

    __automaton = None
    def __get_automaton (self):
        """Link to the L{Automaton} to which the state belongs."""
        return self.__automaton
    def _set_automaton (self, automaton):
        """Method invoked during automaton construction to set state owner."""
        assert self.__automaton is None
        self.__automaton = automaton
        return self
    automaton = property(__get_automaton)

    __symbol = None
    def __get_symbol (self):
        """Application-specific metadata identifying the symbol.

        See also L{match}."""
        return self.__symbol
    symbol = property(__get_symbol)

    __isUnorderedCatenation = None
    def __get_isUnorderedCatenation (self):
        """Indicate whether the state has subautomata for unordered
        catenation.

        To reduce state explosion due to non-determinism, such a state
        executes internal transitions in subautomata until all terms
        have matched or a failure is discovered."""
        return self.__isUnorderedCatenation
    isUnorderedCatenation = property(__get_isUnorderedCatenation)

    __subAutomata = None
    def __get_subAutomata (self):
        """A sequence of sub-automata supporting internal state transitions.

        This will return C{None} unless L{isUnorderedCatenation} is C{True}."""
        return self.__subAutomata
    def _set_subAutomata (self, *automata):
        assert self.__subAutomata is None
        assert self.__isUnorderedCatenation
        self.__subAutomata = automata
    subAutomata = property(__get_subAutomata)

    __isInitial = None
    def __get_isInitial (self):
        """C{True} iff this state may be the first state the automaton enters."""
        return self.__isInitial
    isInitial = property(__get_isInitial)

    __automatonEntryTransitions = None
    def __get_automatonEntryTransitions (self):
        """Return the set of initial transitions allowing entry to the automata through this state.

        These are structurally-permitted transitions only, and must be
        filtered based on the symbol that might trigger the
        transition.  The results are not filtered based on counter
        value, since this value is used to determine how the
        containing automaton might be entered.  Consequently the
        return value is the empty set unless this is an initial state.

        The returned set is closed under entry to sub-automata,
        i.e. it is guaranteed that each transition includes a
        consuming state even if it requires a multi-element chain of
        transitions into subautomata to reach one."""
        if self.__automatonEntryTransitions is None:
            transitions = []
            if self.__isInitial:
                xit = Transition(self, set())
                if self.__subAutomata is None:
                    transitions.append(xit)
                else:
                    for sa in self.__subAutomata:
                        for saxit in sa.initialTransitions:
                            transitions.append(xit.chainTo(saxit.makeEnterAutomatonTransition()))
            self.__automatonEntryTransitions = transitions
        return self.__automatonEntryTransitions
    automatonEntryTransitions = property(__get_automatonEntryTransitions)

    __finalUpdate = None
    def __get_finalUpdate (self):
        """Return the update instructions that must be satisfied for this to be a final state."""
        return self.__finalUpdate
    finalUpdate = property(__get_finalUpdate)

    def subAutomataInitialTransitions (self, sub_automata=None):
        """Return the set of candidate transitions to enter a sub-automaton of this state.

        @param sub_automata: A subset of the sub-automata of this
        state which should contribute to the result.  If C{None}, all
        sub-automata are used.

        @return: A pair C{(nullable, transitions)} where C{nullable}
        is C{True} iff there is at least one sub-automaton that is in
        an accepting state on entry, and C{transitions} is a list of
        L{Transition} instances describing how to reach some state in
        a sub-automaton via a consumed symbol.
        """
        assert self.__subAutomata is not None
        is_nullable = True
        transitions = []
        if sub_automata is None:
            sub_automata = self.__subAutomata
        for sa in sub_automata:
            if not sa.nullable:
                is_nullable = False
            transitions.extend(sa.initialTransitions)
        return (is_nullable, transitions)

    def isAccepting (self, counter_values):
        """C{True} iff this state is an accepting state for the automaton.

        @param counter_values: Counter values that further validate
        whether the requirements of the automaton have been met.

        @return: C{True} if this is an accepting state and the
        counter values relevant at it are satisfied."""
        if self.__finalUpdate is None:
            return False
        return UpdateInstruction.Satisfies(counter_values, self.__finalUpdate)

    __transitionSet = None
    def __get_transitionSet (self):
        """Definitions of viable transitions from this state.

        The transition set of a state is a set of L{Transition} nodes
        identifying a state reachable in a single step from this
        state, and a set of counter updates that must apply if the
        transition is taken.

        These transitions may not in themselves consume a symbol.  For
        example, if the destination state represents a match of an
        L{unordered catenation of terms<All>}, then secondary
        processing must be done to traverse into the automata for
        those terms and identify transitions that include a symbol
        consumption.

        @note: Although conceptually the viable transitions are a set,
        this implementation maintains them in a list so that order is
        preserved when automata processing becomes non-deterministic.
        PyXB is careful to build the transition list so that the
        states are attempted in the order in which they appear in the
        schema that define the automata.
        """
        return self.__transitionSet
    transitionSet = property(__get_transitionSet)

    def _set_transitionSet (self, transition_set):
        """Method invoked during automaton construction to set the
        legal transitions from the state.

        The set of transitions cannot be defined until all states that
        appear in it are available, so the creation of the automaton
        requires that the association of the transition set be
        delayed.  (Though described as a set, the transitions are a
        list where order reflects priority.)

        @param transition_set: a list of pairs where the first
        member is the destination L{State} and the second member is the
        set of L{UpdateInstruction}s that apply when the automaton
        transitions to the destination state."""

        self.__transitionSet = []
        seen = set()
        for xit in transition_set:
            if not (xit in seen):
                seen.add(xit)
                self.__transitionSet.append(xit)

    def match (self, symbol):
        """Return C{True} iff the symbol matches for this state.

        This may be overridden by subclasses when matching by
        equivalence does not work.  Alternatively, if the symbol
        stored in this node is a subclass of L{SymbolMatch_mixin}, then
        its match method will be used.  Otherwise C{symbol} matches
        only if it is equal to the L{symbol} of this state.

        @param symbol: A candidate symbol corresponding to the
        expression symbol for this state.

        @return: C{True} iff C{symbol} is a match for this state.
        """
        if isinstance(self.__symbol, SymbolMatch_mixin):
            return self.__symbol.match(symbol)
        return self.__symbol == symbol

    def __str__ (self):
        return 'S.%x' % (id(self),)

    def _facText (self):
        rv = []
        rv.extend(map(str, self.__transitionSet))
        if self.__finalUpdate is not None:
            if 0 == len(self.__finalUpdate):
                rv.append('Final (no conditions)')
            else:
                rv.append('Final if %s' % (' '.join(map(lambda _ui: str(_ui.counterCondition), self.__finalUpdate))))
        return '\n'.join(rv)

class CounterCondition (object):
    """A counter condition is a range limit on valid counter values.

    Instances of this class serve as keys for the counters that
    represent the configuration of a FAC.  The instance also maintains
    a pointer to application-specific L{metadata}."""

    __min = None
    def __get_min (self):
        """The minimum legal value for the counter.

        This is a non-negative integer."""
        return self.__min
    min = property(__get_min)

    __max = None
    def __get_max (self):
        """The maximum legal value for the counter.

        This is a positive integer, or C{None} to indicate that the
        counter is unbounded."""
        return self.__max
    max = property(__get_max)

    __metadata = None
    def __get_metadata (self):
        """A pointer to application metadata provided when the condition was created."""
        return self.__metadata
    metadata = property(__get_metadata)

    def __init__ (self, min, max, metadata=None):
        """Create a counter condition.

        @param min: The value for L{min}
        @param max: The value for L{max}
        @param metadata: The value for L{metadata}
        """
        self.__min = min
        self.__max = max
        self.__metadata = metadata

    def __hash__ (self):
        return hash(self.__min) ^ hash(self.__max) ^ hash(self.__metadata)

    def __eq__ (self, other):
        return (other is not None) \
            and (self.__min == other.__min) \
            and (self.__max == other.__max) \
            and (self.__metadata == other.__metadata)

    def __ne__ (self, other):
        return not self.__eq__(other)

    def __str__ (self):
        return 'C.%x{%s,%s}' % (id(self), self.min, self.max is not None and self.max or '')

class UpdateInstruction:
    """An update instruction pairs a counter with a mutation of that
    counter.

    The instruction is executed during a transition from one state to
    another, and causes the corresponding counter to be incremented or
    reset.  The instruction may only be applied if doing so does not
    violate the conditions of the counter it affects."""

    __counterCondition = None
    def __get_counterCondition (self):
        """A reference to the L{CounterCondition} identifying the
        counter to be updated.

        The counter condition instance is used as a key to the
        dictionary maintaining current counter values."""
        return self.__counterCondition
    counterCondition = property(__get_counterCondition)

    __doIncrement = None
    def __get_doIncrement (self):
        """C{True} if the counter is to be incremented; C{False} if it is to be reset."""
        return self.__doIncrement
    doIncrement = property(__get_doIncrement)

    # Cached values extracted from counter condition
    __min = None
    __max = None

    def __init__ (self, counter_condition, do_increment):
        """Create an update instruction.

        @param counter_condition: A L{CounterCondition} identifying a
        minimum and maximum value for a counter, and serving as a map
        key for the value of the corresponding counter.

        @param do_increment: C{True} if the update is to increment
        the value of the counter; C{False} if the update is to reset
        the counter.
        """
        self.__counterCondition = counter_condition
        self.__doIncrement = not not do_increment
        self.__min = counter_condition.min
        self.__max = counter_condition.max

    def satisfiedBy (self, counter_values):
        """Implement a component of definition 5 from B{HOV09}.

        The update instruction is satisfied by the counter values if
        its action may be legitimately applied to the value of its
        associated counter.

        @param counter_values: A map from  L{CounterCondition}s to
        non-negative integers

        @return:  C{True} or C{False}
        """
        value = counter_values[self.__counterCondition]
        if self.__doIncrement \
                and (self.__max is not None) \
                and (value >= self.__max):
            return False
        if (not self.__doIncrement) \
                and (value < self.__min):
            return False
        return True

    @classmethod
    def Satisfies (cls, counter_values, update_instructions):
        """Return C{True} iff the counter values satisfy the update
        instructions.

        @param counter_values: A map from L{CounterCondition} to
        integer counter values

        @param update_instructions: A set of L{UpdateInstruction}
        instances

        @return: C{True} iff all instructions are satisfied by the
        values and limits."""
        for psi in update_instructions:
            if not psi.satisfiedBy(counter_values):
                return False
        return True

    def apply (self, counter_values):
        """Apply the update instruction to the provided counter values.

        @param counter_values: A map from L{CounterCondition} to
        integer counter values.  This map is updated in-place."""
        if not self.satisfiedBy(counter_values):
            raise UpdateApplicationError(self, counter_values)
        value = counter_values[self.__counterCondition]
        if self.__doIncrement:
            value += 1
        else:
            value = 1
        counter_values[self.__counterCondition] = value

    @classmethod
    def Apply (cls, update_instructions, counter_values):
        """Apply the update instructions to the counter values.

        @param update_instructions: A set of L{UpdateInstruction}
        instances.

        @param counter_values: A map from L{CounterCondition}
        instances to non-negative integers.  This map is updated
        in-place by applying each instruction in
        C{update_instructions}."""
        for psi in update_instructions:
            psi.apply(counter_values)

    def __hash__ (self):
        return hash(self.__counterCondition) ^ hash(self.__doIncrement)

    def __eq__ (self, other):
        return (other is not None) \
            and (self.__doIncrement == other.__doIncrement) \
            and (self.__counterCondition == other.__counterCondition)

    def __ne__ (self, other):
        return not self.__eq__(other)

    def __str__ (self):
        return '%s %s' % (self.__doIncrement and 'inc' or 'reset', self.__counterCondition)

class Transition (object):
    """Representation of a FAC state transition."""

    __destination = None
    def __get_destination (self):
        """The transition destination state."""
        return self.__destination
    destination = property(__get_destination)

    __updateInstructions = None
    def __get_updateInstructions (self):
        """The set of counter updates that are applied when the transition is taken."""
        return self.__updateInstructions
    updateInstructions = property(__get_updateInstructions)

    __nextTransition = None
    def __get_nextTransition (self):
        """The next transition to apply in this chain.

        C{None} if this is the last transition in the chain."""
        return self.__nextTransition
    nextTransition = property(__get_nextTransition)

    __layerLink = None
    def __get_layerLink (self):
        """A directive relating to changing automaton layer on transition.

        C{None} indicates this transition is from one state to another
        within a single automaton.

        An instance of L{Configuration} is a transition on completion
        of a subautomaton back to the configuration in the parent
        automaton.  The L{destination} is the state in the parent automaton.

        An instance of L{Automaton} requires creation of a
        sub-configuration and initial entry into the automaton.  The
        L{destination} is the state in the sub-automaton.
        """
        return self.__layerLink
    layerLink = property(__get_layerLink)

    def __init__ (self, destination, update_instructions, layer_link=None):
        """Create a transition to a state.

        @param destination: the state into which the transition is
        made

        @param update_instructions: A iterable of L{UpdateInstruction}s
        denoting the changes that must be made to counters as a
        consequence of taking the transition.

        @keyword layer_link: The value for L{layerLink}."""
        self.__destination = destination
        if not isinstance(update_instructions, list):
            update_instructions = list(update_instructions)
        self.__updateInstructions = update_instructions
        self.__layerLink = layer_link

    def consumingState (self):
        """Return the state in this transition chain that must match a symbol."""

        # Transitions to a state with subautomata never consume anything
        if self.__destination.subAutomata is not None:
            if not self.__nextTransition:
                return None
            return self.__nextTransition.consumingState()
        # I don't think there should be subsequent transitions
        assert self.__nextTransition is None
        return self.__destination

    def consumedSymbol (self):
        """Return the L{symbol<State.symbol>} of the L{consumingState}."""
        return self.consumingState().symbol

    def satisfiedBy (self, configuration):
        """Check the transition update instructions against
        configuration counter values.

        This implementation follows layer changes, updating the
        configuration used as counter value source as necessary.

        @param configuration: A L{Configuration} instance containing
        counter data against which update instruction satisfaction is
        checked.

        @return: C{True} iff all update instructions along the
        transition chain are satisfied by their relevant
        configuration."""
        # If we're entering an automaton, we know no subsequent
        # transitions have update instructions
        if isinstance(self.__layerLink, Automaton):
            return True
        # If we're leaving an automaton, switch to the configuration
        # that is relevant to the destination of the transition.
        if isinstance(self.__layerLink, Configuration):
            configuration = self.__layerLink
        assert self.destination.automaton == configuration.automaton
        # Blow chunks if the configuration doesn't satisfy the transition
        if not configuration.satisfies(self):
            return False
        # Otherwise try the next transition, or succeed if there isn't one
        if self.__nextTransition:
            return self.__nextTransition.satisfiedBy(configuration)
        return True

    def apply (self, configuration, clone_map=None):
        """Apply the transitition to a configuration.

        This updates the configuration counter values based on the
        update instructions, and sets the new configuration state.

        @note: If the transition involves leaving a sub-automaton or
        creating a new sub-automaton, the returned configuration
        structure will be different from the one passed in.  You
        should invoke this as::

          cfg = transition.apply(cfg)

        @param configuration: A L{Configuration} of an executing automaton

        @param clone_map: A map from L{Configuration} to
        L{Configuration} reflecting the replacements made when the
        configuration for which the transition was calculated was
        subsequently cloned into the C{configuration} passed into this
        method.  This is only necessary when the transition includes
        layer transitions.

        @return: The resulting configuration
        """
        layer_link = self.__layerLink
        if isinstance(layer_link, Configuration):
            if clone_map is not None:
                layer_link = clone_map[layer_link]
            configuration = layer_link.leaveAutomaton(configuration)
        elif isinstance(layer_link, Automaton):
            configuration = configuration.enterAutomaton(layer_link)
        UpdateInstruction.Apply(self.updateInstructions, configuration._get_counterValues())
        configuration._set_state(self.destination, layer_link is None)
        if self.__nextTransition is None:
            return configuration
        return self.__nextTransition.apply(configuration, clone_map)

    def chainTo (self, next_transition):
        """Duplicate the state and chain the duplicate to a successor
        transition.

        This returns a new transition which applies the operation for
        this transition, then proceeds to apply the next transition in
        the chain.

        @note: The node that is invoking this must not have successor
        transitions.

        @param next_transition: A L{Transition} node describing a
        subsequent transition.

        @return: a clone of this node, augmented with a link to
        C{next_transition}."""
        assert not self.__nextTransition
        head = type(self)(self.__destination, self.__updateInstructions, layer_link=self.__layerLink)
        head.__nextTransition = next_transition
        return head

    def makeEnterAutomatonTransition (self):
        """Replicate the transition as a layer link into its automaton.

        This is used on initial transitions into sub-automata where a
        sub-configuration must be created and recorded."""
        assert self.__layerLink is None
        assert self.__nextTransition is None
        head = type(self)(self.__destination, self.__updateInstructions)
        head.__layerLink = self.__destination.automaton
        return head

    def __hash__ (self):
        rv = hash(self.__destination)
        for ui in self.__updateInstructions:
            rv ^= hash(ui)
        return rv ^ hash(self.__nextTransition) ^ hash(self.__layerLink)

    def __eq__ (self, other):
        return (other is not None) \
            and (self.__destination == other.__destination) \
            and (self.__updateInstructions == other.__updateInstructions) \
            and (self.__nextTransition == other.__nextTransition) \
            and (self.__layerLink == other.__layerLink)

    def __ne__ (self, other):
        return not self.__eq__(other)

    def __str__ (self):
        rv = []
        if isinstance(self.__layerLink, Configuration):
            rv.append('from A%x ' % (id(self.__layerLink.automaton),))
        elif isinstance(self.__layerLink, Automaton):
            rv.append('in A%x ' % (id(self.__layerLink)))
        rv.append('enter %s ' % (self.destination,))
        if (self.consumingState() == self.destination):
            rv.append('via %s ' % (self.destination.symbol,))
        rv.append('with %s' % (' ; '.join(map(str, self.updateInstructions)),))
        if self.__nextTransition:
            rv.append("\n\tthen ")
            rv.append(str(self.__nextTransition))
        return ''.join(rv)

class Configuration_ABC (object):
    """Base class for something that represents an L{Automaton} in
    execution.

    For deterministic automata, this is generally a L{Configuration}
    which records the current automaton state along with its counter
    values.

    For non-deterministic automata, this is a L{MultiConfiguration}
    which records a set of L{Configuration}s."""

    def acceptableSymbols (self):
        """Return the acceptable L{Symbol}s given the current
        configuration.

        This method extracts the symbol from all candidate transitions
        that are permitted based on the current counter values.
        Because transitions are presented in a preferred order, the
        symbols are as well."""
        raise NotImplementedError('%s.acceptableSymbols' % (type(self).__name__,))

    def step (self, symbol):
        """Execute an automaton transition using the given symbol.

        @param symbol: A symbol from the alphabet of the automaton's
        language.  This is a Python value that should be accepted by
        the L{SymbolMatch_mixin.match} method of a L{State.symbol}.
        It is not a L{Symbol} instance.

        @return: The new configuration resulting from the step.

        @raises AutomatonStepError: L{UnrecognizedSymbolError}
        when no transition compatible with C{symbol} is available, and
        L{NondeterministicSymbolError} if C{symbol} admits multiple
        transitions and the subclass does not support
        non-deterministic steps (see L{MultiConfiguration}).

        @warning: If the step entered or left a sub-automaton the
        return value will not be the configuration that was used to
        execute the step.  The proper pattern for using this method
        is::

           cfg = cfg.step(sym)

        """
        raise NotImplementedError('%s.step' % (type(self).__name__,))

class Configuration (Configuration_ABC):
    """The state of an L{Automaton} in execution.

    This combines a state node of the automaton with a set of counter
    values."""

    __state = None
    def __get_state (self):
        """The state of the configuration.

        This is C{None} to indicate an initial state, or one of the underlying automaton's states."""
        return self.__state
    def _set_state (self, state, is_layer_change):
        """Internal state transition interface.

        @param state: the new destination state

        @param is_layer_change: C{True} iff the transition inducing
        the state change involves a layer change.
        """

        # If the new state and old state are the same, the layer
        # change has no effect (we're probably leaving a
        # subconfiguration, and we want to keep the current set of
        # sub-automata.)
        if state == self.__state:
            return

        # Otherwise, discard any unprocessed automata in the former
        # state, set the state, and if the new state has subautomata
        # create a set holding them so they can be processed.
        if is_layer_change:
            self.__subConfiguration = None
            self.__subAutomata = None
        self.__state = state
        if is_layer_change and (state.subAutomata is not None):
            assert self.__subAutomata is None
            self.__subAutomata = list(state.subAutomata)
    state = property(__get_state)

    __counterValues = None
    """The values of the counters.

    This is a map from the CounterCondition instances of the
    underlying automaton to integer values."""
    def _get_counterValues (self):
        return self.__counterValues

    __automaton = None
    def __get_automaton (self):
        return self.__automaton
    automaton = property(__get_automaton)

    __subConfiguration = None
    def __get_subConfiguration (self):
        """Reference to configuration being executed in a sub-automaton.

        C{None} if no sub-automaton is active, else a reference to a
        configuration that is being executed in a sub-automaton.

        Sub-configurations are used to match sub-terms in an
        L{unordered catenation<All>} term.  A configuration may have
        at most one sub-configuration at a time, and the configuration
        will be removed and possibly replaced when the term being
        processed completes."""
        return self.__subConfiguration
    subConfiguration = property(__get_subConfiguration)

    __superConfiguration = None
    def __get_superConfiguration (self):
        """Reference to the configuration for which this is a
        sub-configuration.

        C{None} if no super-automaton is active, else a reference to a
        configuration that is being executed in a super-automaton.

        The super-configuration relation persists for the lifetime of
        the configuration."""
        return self.__superConfiguration
    superConfiguration = property(__get_superConfiguration)

    __subAutomata = None
    def __get_subAutomata (self):
        """A set of automata that must be satisfied before the current state can complete.

        This is used in unordered catenation.  Each sub-automaton
        represents a term in the catenation.  When the configuration
        enters a state with sub-automata, a set containing references
        to those automata is assigned to this attribute.
        Subsequently, until all automata in the state are satisfied,
        transitions can only occur within an active sub-automaton, out
        of the active sub-automaton if it is in an accepting state,
        and into a new sub-automaton if no sub-automaton is active.
        """
        return self.__subAutomata
    def _set_subAutomata (self, automata):
        self.__subAutomata = list(automata)
    subAutomata = property(__get_subAutomata)

    def makeLeaveAutomatonTransition (self):
        """Create a transition back to the containing configuration.

        This is done when a configuration is in an accepting state and
        there are candidate transitions to other states that must be
        considered.  The transition does not consume a symbol."""
        assert self.__superConfiguration is not None
        return Transition(self.__superConfiguration.__state, set(), layer_link=self.__superConfiguration)

    def leaveAutomaton (self, sub_configuration):
        """Execute steps to leave a sub-automaton.

        @param sub_configuration: The configuration associated with
        the automata that has completed.

        @return: C{self}"""
        assert sub_configuration.__superConfiguration == self
        self.__subConfiguration = None
        return self

    def enterAutomaton (self, automaton):
        """Execute steps to enter a new automaton.

        The new automaton is removed from the set of remaining
        automata for the current state, and a new configuration
        created.  No transition is made in that new configuration.

        @param automaton: The automaton to be entered

        @return: The configuration that executes the new automaton as
        a sub-configuration of C{self}."""
        assert self.__subConfiguration is None
        assert self.__subAutomata is not None
        self.__subAutomata.remove(automaton)
        self.__subConfiguration = Configuration(automaton)
        self.__subConfiguration.__superConfiguration = self
        return self.__subConfiguration

    def satisfies (self, transition):
        return UpdateInstruction.Satisfies(self.__counterValues, transition.updateInstructions)

    def reset (self):
        fac = self.__automaton
        self.__state = None
        self.__counterValues = dict(zip(fac.counterConditions, len(fac.counterConditions) * (1,)))
        self.__subConfiguration = None
        self.__subAutomata = None

    def candidateTransitions (self, symbol=None):
        """Return list of viable transitions on C{symbol}

        The transitions that are structurally permitted from this
        state, in order, filtering out those transitions where the
        update instruction is not satisfied by the configuration
        counter values and optionally those for which the symbol does
        not match.

        @param symbol: A symbol through which a transition from this
        state is intended.  A value of C{None} indicates that the set
        of transitions should ignore the symbol; candidates are still
        filtered based on the counter state of the configuration.

        @return: A list of L{Transition} instances permitted from the
        current configuration.  If C{symbol} is not C{None},
        transitions that would not accept the symbol are excluded.
        Any transition that would require an unsatisfied counter
        update is also excluded.  Non-deterministic automata may
        result in a lits with multiple members. """

        fac = self.__automaton
        transitions = []
        if symbol is None:
            match_filter = lambda _xit: True
        else:
            match_filter = lambda _xit: _xit.consumingState().match(symbol)
        update_filter = lambda _xit: _xit.satisfiedBy(self)

        if self.__state is None:
            # Special-case the initial entry to the topmost configuration
            transitions.extend(fac.initialTransitions)
        elif (self.__subConfiguration is not None) and not self.__subConfiguration.isAccepting():
            # If there's an active subconfiguration that is not in an
            # accepting state, we can't do anything at this level.
            pass
        else:
            # Normally include transitions at this level, but in some
            # cases they are not permitted.
            include_local = True
            if self.__subAutomata:
                # Disallow transitions in this level if there are
                # subautomata that require symbols before a transition
                # out of this node is allowed.
                (include_local, sub_initial) = self.__state.subAutomataInitialTransitions(self.__subAutomata)
                transitions.extend(map(lambda _xit: _xit.makeEnterAutomatonTransition(), sub_initial))
            if include_local:
                # Transitions within this layer
                for xit in filter(update_filter, self.__state.transitionSet):
                    if xit.consumingState() is not None:
                        transitions.append(xit)
                    else:
                        # The transition did not consume a symbol, so we have to find
                        # one that does, from among the subautomata of the destination.
                        # We do not care if the destination is nullable; alternatives
                        # to it are already being handled with different transitions.
                        (_, sub_initial) = xit.destination.subAutomataInitialTransitions()
                        transitions.extend(map(lambda _xit: xit.chainTo(_xit.makeEnterAutomatonTransition()), sub_initial))
                if (self.__superConfiguration is not None) and self.isAccepting():
                    # Transitions that leave this automaton
                    lxit = self.makeLeaveAutomatonTransition()
                    supxit = self.__superConfiguration.candidateTransitions(symbol)
                    transitions.extend(map(lambda _sx: lxit.chainTo(_sx), supxit))
        assert len(frozenset(transitions)) == len(transitions)
        return list(filter(update_filter, filter(match_filter, transitions)))

    def acceptableSymbols (self):
        return [ _xit.consumedSymbol() for _xit in self.candidateTransitions()]

    def step (self, symbol):
        transitions = self.candidateTransitions(symbol)
        if 0 == len(transitions):
            raise UnrecognizedSymbolError(self, symbol)
        if 1 < len(transitions):
            raise NondeterministicSymbolError(self, symbol)
        return transitions[0].apply(self)

    def isInitial (self):
        """Return C{True} iff no transitions have ever been made."""
        return self.__state is None

    def isAccepting (self):
        """Return C{True} iff the automaton is in an accepting state."""
        if self.__state is not None:
            # Any active sub-configuration must be accepting
            if (self.__subConfiguration is not None) and not self.__subConfiguration.isAccepting():
                return False
            # Any unprocessed sub-automata must be nullable
            if self.__subAutomata is not None:
                if not functools.reduce(operator.and_, map(lambda _sa: _sa.nullable, self.__subAutomata), True):
                    return False
            # This state must be accepting
            return self.__state.isAccepting(self.__counterValues)
        # Accepting without any action requires nullable automaton
        return self.__automaton.nullable

    def __init__ (self, automaton, super_configuration=None):
        self.__automaton = automaton
        self.__superConfiguration = super_configuration
        self.reset()

    def clone (self, clone_map=None):
        """Clone a configuration and its descendents.

        This is used for parallel execution where a configuration has
        multiple candidate transitions and must follow all of them.
        It clones the entire chain of configurations through
        multiple layers.

        @param clone_map: Optional map into which the translation from
        the original configuration object to the corresponding cloned
        configuration object can be reconstructed, e.g. when applying
        a transition that includes automata exits referencing
        superconfigurations from the original configuration.
        """
        if clone_map is None:
            clone_map = {}
        root = self
        while root.__superConfiguration is not None:
            root = root.__superConfiguration
        root = root._clone(clone_map, None)
        return clone_map.get(self)

    def _clone (self, clone_map, super_configuration):
        assert not self in clone_map
        other = type(self)(self.__automaton)
        clone_map[self] = other
        other.__state = self.__state
        other.__counterValues = self.__counterValues.copy()
        other.__superConfiguration = super_configuration
        if self.__subAutomata is not None:
            other.__subAutomata = self.__subAutomata[:]
            if self.__subConfiguration:
                other.__subConfiguration = self.__subConfiguration._clone(clone_map, other)
        return other

    def __str__ (self):
        return '%s: %s' % (self.__state, ' ; '.join([ '%s=%u' % (_c,_v) for (_c,_v) in six.iteritems(self.__counterValues)]))

class MultiConfiguration (Configuration_ABC):
    """Support parallel execution of state machine.

    This holds a set of configurations, and executes each transition
    on each one.  Configurations which fail to accept a step are
    silently dropped; only if this results in no remaining
    configurations will L{UnrecognizedSymbolError} be raised.  If a
    step admits multiple valid transitions, a configuration is added
    for each one.

    See L{pyxb.binding.content.AutomatonConfiguration} for an
    alternative solution which holds actions associated with the
    transition until the non-determinism is resolved."""

    __configurations = None

    def __init__ (self, configuration):
        self.__configurations = [ configuration]

    def acceptableSymbols (self):
        acceptable = []
        for cfg in self.__configurations:
            acceptable.extend(cfg.acceptableSymbols())
        return acceptable

    def step (self, symbol):
        next_configs = []
        for cfg in self.__configurations:
            transitions = cfg.candidateTransitions(symbol)
            if 0 == len(transitions):
                pass
            elif 1 == len(transitions):
                next_configs.append(transitions[0].apply(cfg))
            else:
                for transition in transitions:
                    clone_map = {}
                    ccfg = cfg.clone(clone_map)
                    next_configs.append(transition.apply(ccfg, clone_map))
        if 0 == len(next_configs):
            raise UnrecognizedSymbolError(self, symbol)
        assert len(frozenset(next_configs)) == len(next_configs)
        self.__configurations = next_configs
        return self

    def acceptingConfigurations (self):
        """Return the set of configurations that are in an accepting state.

        Note that some of the configurations may be within a
        sub-automaton; their presence in the return value is because
        the root configuration is also accepting."""
        accepting = []
        for cfg in self.__configurations:
            rcfg = cfg
            # Rule out configurations that are accepting within their
            # automaton, but not in the containing automaton.
            while rcfg.superConfiguration is not None:
                rcfg = rcfg.superConfiguration
            if rcfg.isAccepting():
                accepting.append(cfg)
        return accepting

class Automaton (object):
    """Representation of a Finite Automaton with Counters.

    This has all the standard FAC elements, plus links to other
    states/automata as required to support the nested automata
    construct used for matching unordered catenation terms."""
    __states = None
    def __get_states (self):
        """The set of L{State}s in the automaton.

        These correspond essentially to marked symbols in the original
        regular expression, or L{element
        declarations<pyxb.xmlschema.structures.ElementDeclaration>} in
        an XML schema.

        @note: These are conceptually a set and are stored that way.
        When an L{Automaton} is constructed the incoming states should
        be passed as a list so the calculated initial transitions are
        executed in a deterministic order."""
        return self.__states
    states = property(__get_states)

    __counterConditions = None
    def __get_counterConditions (self):
        """The set of L{CounterCondition}s in the automaton.

        These are marked positions in the regular expression, or
        L{particles<pyxb.xmlschema.structures.Particle>} in an XML
        schema, paired with their occurrence constraints."""
        return self.__counterConditions
    counterConditions = property(__get_counterConditions)

    __nullable = None
    def __get_nullable (self):
        """C{True} iff the automaton accepts the empty string."""
        return self.__nullable
    nullable = property(__get_nullable)

    __initialTransitions = None
    def __get_initialTransitions (self):
        """The set of transitions that may be made to enter the automaton.

        These are full transitions, including chains into subautomata
        if an initial state represents a node with sub-automata.

        @note: As with L{State.transitionSet}, the set is represented
        as a list to preserve priority when resolving
        non-deterministic matches."""
        return self.__initialTransitions
    initialTransitions = property(__get_initialTransitions)

    __containingState = None
    def __get_containingState (self):
        """The L{State} instance for which this is a sub-automaton.

        C{None} if this is not a sub-automaton."""
        return self.__containingState
    containingState = property(__get_containingState)

    __finalStates = None
    def __get_finalStates (self):
        """The set of L{State} members which can terminate a match."""
        return self.__finalStates
    finalStates = property(__get_finalStates)

    def __init__ (self, states, counter_conditions, nullable, containing_state=None):
        self.__states = frozenset(states)
        for st in self.__states:
            st._set_automaton(self)
        self.__counterConditions = frozenset(counter_conditions)
        self.__nullable = nullable
        self.__containingState = containing_state
        xit = []
        fnl = set()
        # Iterate over states, not self.__states, in case the input was a list.
        # This way we preserve the priority for initial transitions.
        for s in states:
            if s.isInitial:
                xit.extend(s.automatonEntryTransitions)
            if s.finalUpdate is not None:
                fnl.add(s)
        self.__initialTransitions = xit
        self.__finalStates = frozenset(fnl)

    def newConfiguration (self):
        """Return a new L{Configuration} instance for this automaton."""
        return Configuration(self)

    def __str__ (self):
        rv = []
        rv.append('sigma = %s' % (' '.join(map(lambda _s: str(_s.symbol), self.__states))))
        rv.append('states = %s' % (' '.join(map(str, self.__states))))
        for s in self.__states:
            if s.subAutomata is not None:
                for i in xrange(len(s.subAutomata)):
                    rv.append('SA %s.%u is %x:\n  ' % (str(s), i, id(s.subAutomata[i])) + '\n  '.join(str(s.subAutomata[i]).split('\n')))
        rv.append('counters = %s' % (' '.join(map(str, self.__counterConditions))))
        rv.append('initial = %s' % (' ; '.join([ '%s on %s' % (_s, _s.symbol) for _s in filter(lambda _s: _s.isInitial, self.__states)])))
        rv.append('initial transitions:\n%s' % ('\n'.join(map(str, self.initialTransitions))))
        rv.append('States:')
        for s in self.__states:
            rv.append('%s: %s' % (s, s._facText()))
        return '\n'.join(rv)

class Node (object):
    """Abstract class for any node in the term tree.

    In its original form a B{position} (C{pos}) is a tuple of
    non-negative integers comprising a path from a node in the term
    tree.  It identifies a node in the tree.  After the FAC has been
    constructed, only positions that are leaf nodes in the term tree
    remain, and the corresponding symbol value (Python instance) is
    used as the position.

    An B{update instruction} (C{psi}) is a map from positions to
    either L{Node.RESET} or L{Node.INCREMENT}.  It identifies actions
    to be taken on the counter states corresponding to the positions
    in its domain.

    A B{transition} is a pair containing a position and an update
    instruction.  It identifies a potential next node in the state and
    the updates that are to be performed if the transition is taken.

    A B{follow value} is a map from a position to a set of transitions
    that may originate from the pos.  This set is represented as a
    Python list since update instructions are dicts and cannot be
    hashed.
    """

    _Precedence = None
    """An integral value used for parenthesizing expressions.

    A subterm that has a precedence less than that of its containing
    term must be enclosed in parentheses when forming a text
    expression representing the containing term."""

    RESET = False
    """An arbitrary value representing reset of a counter."""

    INCREMENT = True
    """An arbitrary value representing increment of a counter."""

    def __init__ (self, **kw):
        """Create a FAC term-tree node.

        @keyword metadata: Any application-specific metadata retained in
        the term tree for transfer to the resulting automaton."""
        self.__metadata = kw.get('metadata')

    def clone (self, *args, **kw):
        """Create a deep copy of the node.

        All term-tree--related attributes and properties are replaced
        with deep clones.  Other attributes are preserved.

        @param args: A tuple of arguments to be passed to the instance
        constructor.

        @param kw: A dict of keywords to be passed to the instance
        constructor.

        @note: Subclasses should pre-extend this method to augment the
        C{args} and C{kw} parameters as necessary to match the
        expectations of the C{__init__} method of the class being
        cloned."""
        kw.setdefault('metadata', self.metadata)
        return type(self)(*args, **kw)

    __metadata = None
    def __get_metadata (self):
        """Application-specific metadata provided during construction."""
        return self.__metadata
    metadata = property(__get_metadata)

    __first = None
    def __get_first (self):
        """The I{first} set for the node.

        This is the set of positions leading to symbols that can
        appear first in a string matched by an execution starting at
        the node."""
        if self.__first is None:
            self.__first = frozenset(self._first())
        return self.__first
    first = property(__get_first)

    def _first (self):
        """Abstract method that defines L{first} for the subclass.

        The return value should be an iterable of tuples of integers
        denoting paths from this node through the term tree to a
        symbol."""
        raise NotImplementedError('%s.first' % (type(self).__name__,))

    __last = None
    def __get_last (self):
        """The I{last} set for the node.

        This is the set of positions leading to symbols that can
        appear last in a string matched by an execution starting at
        the node."""
        if self.__last is None:
            self.__last = frozenset(self._last())
        return self.__last
    last = property(__get_last)

    def _last (self):
        """Abstract method that defines L{last} for the subclass.

        The return value should be an iterable of tuples of integers
        denoting paths from this node through the term tree to a
        symbol."""
        raise NotImplementedError('%s.last' % (type(self).__name__,))

    __nullable = None
    def __get_nullable (self):
        """C{True} iff the empty string is accepted by this node."""
        if self.__nullable is None:
            self.__nullable = self._nullable()
        return self.__nullable
    nullable = property(__get_nullable)

    def _nullable (self):
        """Abstract method that defines L{nullable} for the subclass.

        The return value should be C{True} or C{False}."""
        raise NotImplementedError('%s.nullable' % (type(self).__name__,))

    __follow = None
    def __get_follow (self):
        """The I{follow} map for the node."""
        if self.__follow is None:
            self.__follow = self._follow()
        return self.__follow
    follow = property(__get_follow)

    def _follow (self):
        """Abstract method that defines L{follow} for the subclass.

        The return value should be a map from tuples of integers (positions)
        to a list of transitions, where a transition is a position and
        an update instruction."""
        raise NotImplementedError('%s.follow' % (type(self).__name__,))

    def reset (self):
        """Reset any term-tree state associated with the node.

        Any change to the structure of the term tree in which the node
        appears invalidates memoized first/follow sets and related
        information.  This method clears all that data so it can be
        recalculated.  It does not clear the L{metadata} link, or any
        existing structural data."""
        self.__first = None
        self.__last = None
        self.__nullable = None
        self.__follow = None
        self.__counterPositions = None

    def walkTermTree (self, pre, post, arg):
        """Utility function for term tree processing.

        @param pre: a callable that, unless C{None}, is invoked at
        each node C{n} with parameters C{n}, C{pos}, and C{arg}, where
        C{pos} is the tuple of integers identifying the path from the
        node at on which this method was invoked to the node being
        processed.  The invocation occurs before processing any
        subordinate nodes.

        @param post: as with C{pre} but invocation occurs after
        processing any subordinate nodes.

        @param arg: a value passed to invocations of C{pre} and
        C{post}."""
        self._walkTermTree((), pre, post, arg)

    def _walkTermTree (self, position, pre, post, arg):
        """Abstract method implementing L{walkTermTree} for the subclass."""
        raise NotImplementedError('%s.walkTermTree' % (type(self).__name__,))

    __posNodeMap = None
    def __get_posNodeMap (self):
        """A map from positions to nodes in the term tree."""
        if self.__posNodeMap is None:
            pnm = { }
            self.walkTermTree(lambda _n,_p,_a: _a.setdefault(_p, _n), None, pnm)
            self.__posNodeMap = pnm
        return self.__posNodeMap
    posNodeMap = property(__get_posNodeMap)

    __nodePosMap = None
    def __get_nodePosMap (self):
        """A map from nodes to their position in the term tree."""
        if self.__nodePosMap is None:
            npm = {}
            for (p,n) in six.iteritems(self.posNodeMap):
                npm[n] = p
            self.__nodePosMap = npm
        return self.__nodePosMap
    nodePosMap = property(__get_nodePosMap)

    @classmethod
    def _PosConcatPosSet (cls, pos, pos_set):
        """Implement definition 11.1 in B{HOV09}."""
        return frozenset([ pos + _mp for _mp in pos_set ])

    @classmethod
    def _PosConcatUpdateInstruction (cls, pos, psi):
        """Implement definition 11.2 in B{HOV09}"""
        rv = {}
        for (q, v) in six.iteritems(psi):
            rv[pos + q] = v
        return rv

    @classmethod
    def _PosConcatTransitionSet (cls, pos, transition_set):
        """Implement definition 11.3 in B{HOV09}"""
        ts = []
        for (q, psi) in transition_set:
            ts.append((pos + q, cls._PosConcatUpdateInstruction(pos, psi) ))
        return ts

    def __resetAndValidate (self, node, pos, visited_nodes):
        if node in visited_nodes:
            raise InvalidTermTreeError(self, node)
        node.reset()
        visited_nodes.add(node)

    def buildAutomaton (self, state_ctor=State, ctr_cond_ctor=CounterCondition, containing_state=None):
        # Validate that the term tree is in fact a tree.  A DAG does
        # not work.  If the tree had cycles, the automaton build
        # wouldn't even return.
        self.walkTermTree(self.__resetAndValidate, None, set())

        counter_map = { }
        for pos in self.counterPositions:
            nci = self.posNodeMap.get(pos)
            assert isinstance(nci, NumericalConstraint)
            assert nci not in counter_map
            counter_map[pos] = ctr_cond_ctor(nci.min, nci.max, nci.metadata)
        counters = list(six.itervalues(counter_map))

        state_map = { }
        for pos in six.iterkeys(self.follow):
            sym = self.posNodeMap.get(pos)
            assert isinstance(sym, LeafNode)
            assert sym not in state_map

            # The state may be an initial state if it is in the first
            # set for the root of the term tree.
            is_initial = pos in self.first

            # The state may be a final state if it is nullable or is
            # in the last set of the term tree.
            final_update = None
            if (() == pos and sym.nullable) or (pos in self.last):
                # Acceptance is further constrained by the counter
                # values satisfying an update rule that would reset
                # all counters that are relevant at the state.
                final_update = set()
                for nci in map(counter_map.get, self.counterSubPositions(pos)):
                    final_update.add(UpdateInstruction(nci, False))
            state_map[pos] = state_ctor(sym.metadata, is_initial=is_initial, final_update=final_update, is_unordered_catenation=isinstance(sym, All))
            if isinstance(sym, All):
                state_map[pos]._set_subAutomata(*map(lambda _s: _s.buildAutomaton(state_ctor, ctr_cond_ctor, containing_state=state_map[pos]), sym.terms))
        states = list(six.itervalues(state_map))

        for (spos, transition_set) in six.iteritems(self.follow):
            src = state_map[spos]
            phi = []
            for (dpos, psi) in transition_set:
                dst = state_map[dpos]
                uiset = set()
                for (counter, action) in six.iteritems(psi):
                    uiset.add(UpdateInstruction(counter_map[counter], self.INCREMENT == action))
                phi.append(Transition(dst, uiset))
            src._set_transitionSet(phi)

        return Automaton(states, counters, self.nullable, containing_state=containing_state)

    __counterPositions = None
    def __get_counterPositions (self):
        """Implement definition 13.1 from B{HOV09}.

        The return value is the set of all positions leading to
        L{NumericalConstraint} nodes for which either the minimum
        value is not 1 or the maximum value is not unbounded."""
        if self.__counterPositions is None:
            cpos = []
            self.walkTermTree(lambda _n,_p,_a: \
                                  isinstance(_n, NumericalConstraint) \
                                  and ((1 != _n.min) \
                                       or (_n.max is not None)) \
                                  and _a.append(_p),
                              None, cpos)
            self.__counterPositions = frozenset(cpos)
        return self.__counterPositions
    counterPositions = property(__get_counterPositions)

    def counterSubPositions (self, pos):
        """Implement definition 13.2 from B{HOV09}.

        This is the subset of L{counterPositions} that occur along the
        path to C{pos}."""
        rv = set()
        for cpos in self.counterPositions:
            if cpos == pos[:len(cpos)]:
                rv.add(cpos)
        return frozenset(rv)

    def _facToString (self):
        """Obtain a description of the FAC in text format.

        This is a diagnostic tool, returning first, last, and follow
        maps using positions."""
        rv = []
        rv.append('r\t= %s' % (str(self),))
        states = list(six.iterkeys(self.follow))
        rv.append('sym(r)\t= %s' % (' '.join(map(str, map(self.posNodeMap.get, states)))))
        rv.append('first(r)\t= %s' % (' '.join(map(str, self.first))))
        rv.append('last(r)\t= %s' % (' '.join(map(str, self.last))))
        rv.append('C\t= %s' % (' '.join(map(str, self.counterPositions))))
        for pos in self.first:
            rv.append('qI(%s) -> %s' % (self.posNodeMap[pos].metadata, str(pos)))
        for spos in states:
            for (dpos, transition_set) in self.follow[spos]:
                dst = self.posNodeMap[dpos]
                uv = []
                for (c, u) in six.iteritems(transition_set):
                    uv.append('%s %s' % (u == self.INCREMENT and "inc" or "rst", str(c)))
                rv.append('%s -%s-> %s ; %s' % (str(spos), dst.metadata, str(dpos), ' ; '.join(uv)))
        return '\n'.join(rv)

class MultiTermNode (Node):
    """Intermediary for nodes that have multiple child nodes."""

    __terms = None
    def __get_terms (self):
        """The set of subordinate terms of the current node."""
        return self.__terms
    terms = property(__get_terms)

    def __init__ (self, *terms, **kw):
        """Term that collects an ordered sequence of terms.

        The terms are provided as arguments.  All must be instances of
        a subclass of L{Node}."""
        super(MultiTermNode, self).__init__(**kw)
        self.__terms = terms

    def clone (self):
        cterms = map(lambda _s: _s.clone(), self.__terms)
        return super(MultiTermNode, self).clone(*cterms)

    def _walkTermTree (self, position, pre, post, arg):
        if pre is not None:
            pre(self, position, arg)
        for c in xrange(len(self.__terms)):
            self.__terms[c]._walkTermTree(position + (c,), pre, post, arg)
        if post is not None:
            post(self, position, arg)

class LeafNode (Node):
    """Intermediary for nodes that have no child nodes."""
    def _first (self):
        return [()]
    def _last (self):
        return [()]
    def _nullable (self):
        return False
    def _follow (self):
        return { (): frozenset() }

    def _walkTermTree (self, position, pre, post, arg):
        if pre is not None:
            pre(self, position, arg)
        if post is not None:
            post(self, position, arg)

class NumericalConstraint (Node):
    """A term with a numeric range constraint.

    This corresponds to a "particle" in the XML Schema content model."""

    _Precedence = -1

    __min = None
    def __get_min (self):
        return self.__min
    min = property(__get_min)

    __max = None
    def __get_max (self):
        return self.__max
    max = property(__get_max)

    __term = None
    def __get_term (self):
        return self.__term
    term = property(__get_term)

    def __init__ (self, term, min=0, max=1, **kw):
        """Term with a numerical constraint.

        @param term: A term, the number of appearances of which is
        constrained in this term.
        @type term: L{Node}

        @keyword min: The minimum number of occurrences of C{term}.
        The value must be non-negative.

        @keyword max: The maximum number of occurrences of C{term}.
        The value must be positive (in which case it must also be no
        smaller than C{min}), or C{None} to indicate an unbounded
        number of occurrences."""
        super(NumericalConstraint, self).__init__(**kw)
        self.__term = term
        self.__min = min
        self.__max = max

    def clone (self):
        return super(NumericalConstraint, self).clone(self.__term, self.__min, self.__max)

    def _first (self):
        return [ (0,) + _fc for _fc in self.__term.first ]

    def _last (self):
        return [ (0,) + _lc for _lc in self.__term.last ]

    def _nullable (self):
        return (0 == self.__min) or self.__term.nullable

    def _follow (self):
        rv = {}
        pp = (0,)
        last_r1 = set(self.__term.last)
        for (q, transition_set) in six.iteritems(self.__term.follow):
            rv[pp+q] = self._PosConcatTransitionSet(pp, transition_set)
            if q in last_r1:
                last_r1.remove(q)
                for sq1 in self.__term.first:
                    q1 = pp+sq1
                    psi = {}
                    for p1 in self.__term.counterSubPositions(q):
                        psi[pp+p1] = self.RESET
                    if (1 != self.min) or (self.max is not None):
                        psi[()] = self.INCREMENT
                    rv[pp+q].append((q1, psi))
        assert not last_r1
        return rv

    def _walkTermTree (self, position, pre, post, arg):
        if pre is not None:
            pre(self, position, arg)
        self.__term._walkTermTree(position + (0,), pre, post, arg)
        if post is not None:
            post(self, position, arg)

    def __str__ (self):
        rv = str(self.__term)
        if self.__term._Precedence < self._Precedence:
            rv = '(' + rv + ')'
        rv += '^(%u,' % (self.__min,)
        if self.__max is not None:
            rv += '%u' % (self.__max)
        return rv + ')'

class Choice (MultiTermNode):
    """A term that may be any one of a set of terms.

    This term matches if any one of its contained terms matches."""

    _Precedence = -3

    def __init__ (self, *terms, **kw):
        """Term that selects one of a set of terms.

        The terms are provided as arguments.  All must be instances of
        a subclass of L{Node}."""
        super(Choice, self).__init__(*terms, **kw)

    def _first (self):
        rv = set()
        for c in xrange(len(self.terms)):
            rv.update([ (c,) + _fc for _fc in self.terms[c].first])
        return rv

    def _last (self):
        rv = set()
        for c in xrange(len(self.terms)):
            rv.update([ (c,) + _lc for _lc in self.terms[c].last])
        return rv

    def _nullable (self):
        for t in self.terms:
            if t.nullable:
                return True
        return False

    def _follow (self):
        rv = {}
        for c in xrange(len(self.terms)):
            for (q, transition_set) in six.iteritems(self.terms[c].follow):
                pp = (c,)
                rv[pp + q] = self._PosConcatTransitionSet(pp, transition_set)
        return rv

    def __str__ (self):
        elts = []
        for t in self.terms:
            if t._Precedence < self._Precedence:
                elts.append('(' + str(t) + ')')
            else:
                elts.append(str(t))
        return '+'.join(elts)

class Sequence (MultiTermNode):
    """A term that is an ordered sequence of terms."""

    _Precedence = -2

    def __init__ (self, *terms, **kw):
        """Term that collects an ordered sequence of terms.

        The terms are provided as arguments.  All must be instances of
        a subclass of L{Node}."""
        super(Sequence, self).__init__(*terms, **kw)

    def _first (self):
        rv = set()
        c = 0
        while c < len(self.terms):
            t = self.terms[c]
            rv.update([ (c,) + _fc for _fc in t.first])
            if not t.nullable:
                break
            c += 1
        return rv

    def _last (self):
        rv = set()
        c = len(self.terms) - 1
        while 0 <= c:
            t = self.terms[c]
            rv.update([ (c,) + _lc for _lc in t.last])
            if not t.nullable:
                break
            c -= 1
        return rv

    def _nullable (self):
        for t in self.terms:
            if not t.nullable:
                return False
        return True

    def _follow (self):
        rv = {}
        for c in xrange(len(self.terms)):
            pp = (c,)
            for (q, transition_set) in six.iteritems(self.terms[c].follow):
                rv[pp + q] = self._PosConcatTransitionSet(pp, transition_set)
        for c in xrange(len(self.terms)-1):
            t = self.terms[c]
            pp = (c,)
            # Link from the last of one term to the first of the next term.
            # Repeat while the destination term is nullable and there are
            # successor terms.
            for q in t.last:
                psi = {}
                for p1 in t.counterSubPositions(q):
                    psi[pp + p1] = self.RESET
                nc = c
                while nc+1 < len(self.terms):
                    nc += 1
                    nt = self.terms[nc]
                    for sq1 in nt.first:
                        q1 = (nc,) + sq1
                        rv[pp+q].append((q1, psi))
                    if not nt.nullable:
                        break
        return rv

    def __str__ (self):
        elts = []
        for t in self.terms:
            if t._Precedence < self._Precedence:
                elts.append('(' + str(t) + ')')
            else:
                elts.append(str(t))
        return '.'.join(elts)

class All (MultiTermNode, LeafNode):
    """A term that is an unordered sequence of terms.

    Note that the inheritance structure for this node is unusual.  It
    has multiple children when it is treated as a term tree, but is
    considered a leaf node when constructing an automaton.
    """

    _Precedence = 0

    def __init__ (self, *terms, **kw):
        """Term that collects an unordered sequence of terms.

        The terms are provided as arguments.  All must be instances of
        a subclass of L{Node}."""
        super(All, self).__init__(*terms, **kw)

    def _nullable (self):
        for t in self.terms:
            if not t.nullable:
                return False
        return True

    @classmethod
    def CreateTermTree (cls, *terms):
        """Create a term tree that implements unordered catenation of
        the terms.

        This expansion results in a standard choice/sequence term
        tree, at the cost of quadratic state expansion because terms
        are L{cloned<Node.clone>} as required to satisfy the tree
        requirements of the term tree.

        @param terms: The tuple of terms that are elements of an
        accepted sequence.

        @return: A term tree comprising a choice between sequences
        that connect each term to the unordered catenation of the
        remaining terms."""
        if 1 == len(terms):
            return terms[0]
        disjuncts = []
        for i in xrange(len(terms)):
            n = terms[i]
            rem = map(lambda _s: _s.clone(), terms[:i] + terms[i+1:])
            disjuncts.append(Sequence(n, cls.CreateTermTree(*rem)))
        return Choice(*disjuncts)

    def __str__ (self):
        return six.u('&(') + six.u(',').join([str(_t) for _t in self.terms]) + ')'

class Symbol (LeafNode):
    """A leaf term that is a symbol.

    The symbol is represented by the L{metadata} field."""

    _Precedence = 0

    def __init__ (self, symbol, **kw):
        kw['metadata'] = symbol
        super(Symbol, self).__init__(**kw)

    def clone (self):
        return super(Symbol, self).clone(self.metadata)

    def __str__ (self):
        return str(self.metadata)
