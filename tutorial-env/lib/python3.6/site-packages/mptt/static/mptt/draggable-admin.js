/* global django */

// IE<9 lacks Array.prototype.indexOf
if (!Array.prototype.indexOf) {
    Array.prototype.indexOf = function(needle) {
        for (var i=0, l=this.length; i<l; ++i) {
            if (this[i] === needle) return i;
        }
        return -1;
    };
}

// https://github.com/jquery/jquery-ui/blob/master/ui/disable-selection.js
django.jQuery.fn.extend({
    disableSelection: (function() {
        var eventType = 'onselectstart' in document.createElement('div') ? 'selectstart' : 'mousedown';

        return function() {
            return this.on(eventType + '.ui-disableSelection', function(event) {
                event.preventDefault();
            });
        };
    })(),

    enableSelection: function() {
        return this.off('.ui-disableSelection');
    }
});


django.jQuery(function($){
    // We are not on a changelist it seems.
    if (!document.getElementById('result_list')) return;

    var DraggableMPTTAdmin = null;

    function isExpandedNode(id) {
        return DraggableMPTTAdmin.collapsedNodes.indexOf(id) == -1;
    }

    function markNodeAsExpanded(id) {
        // remove itemId from array of collapsed nodes
        var idx = DraggableMPTTAdmin.collapsedNodes.indexOf(id);
        if(idx >= 0)
            DraggableMPTTAdmin.collapsedNodes.splice(idx, 1);
    }

    function markNodeAsCollapsed(id) {
        if(isExpandedNode(id))
            DraggableMPTTAdmin.collapsedNodes.push(id);
    }

    function treeNode(pk) {
        return $('.tree-node[data-pk="' + pk + '"]');
    }

    // toggle children
    function doToggle(id, show) {
        var children = DraggableMPTTAdmin.treeStructure[id] || [];
        for (var i=0; i<children.length; ++i) {
            var childId = children[i];
            if(show) {
                treeNode(childId).closest('tr').show();
                // only reveal children if current node is not collapsed
                if(isExpandedNode(childId)) {
                    doToggle(childId, show);
                }
            } else {
                treeNode(childId).closest('tr').hide();
                // always recursively hide children
                doToggle(childId, show);
            }
        }
    }

    function rowLevel($row) {
        try {
            return $row.find('.tree-node').data('level') || 0;
        } catch (e) {
            return 0;
        }
    }

    /*
     * FeinCMS Drag-n-drop tree reordering.
     * Based upon code by bright4 for Radiant CMS, rewritten for
     * FeinCMS by Bjorn Post.
     *
     * September 2010
     */
    $.extend($.fn.feinTree = function() {
        $.each(DraggableMPTTAdmin.treeStructure, function(key, value) {
          treeNode(key).addClass('children');
        });

        $('div.drag-handle').bind('mousedown', function(event) {
            var BEFORE = 'before';
            var AFTER = 'after';
            var CHILD = 'child';
            var CHILD_PAD = DraggableMPTTAdmin.levelIndent;
            var originalRow = $(event.target).closest('tr');
            var rowHeight = originalRow.height();
            var moveTo = new Object();
            var resultListWidth = $('#result_list').width();

            $('body').addClass('dragging').disableSelection().bind('mousemove', function(event) {
                // Remove focus
                originalRow.blur();

                // attach dragged item to mouse
                var cloned = originalRow.html();
                if($('#ghost').length == 0) {
                    $('<div id="ghost"></div>').appendTo('body');
                }
                $('#ghost').html(cloned).css({
                    'opacity': .8,
                    'position': 'absolute',
                    'top': event.pageY,
                    'left': event.pageX - 30,
                    'width': 600
                });

                // check on edge of screen
                if(event.pageY+100 > $(window).height()+$(window).scrollTop()) {
                    $('html,body').stop().animate({scrollTop: $(window).scrollTop()+250 }, 500);
                } else if(event.pageY-50 < $(window).scrollTop()) {
                    $('html,body').stop().animate({scrollTop: $(window).scrollTop()-250 }, 500);
                }

                // check if drag-line element already exists, else append
                if($('#drag-line').length < 1) {
                    $('body').append('<div id="drag-line"><span></span></div>');
                }

                // loop trough all rows
                $('tr', originalRow.parent()).each(function(index, el) {
                    var element = $(el),
                        top = element.offset().top,
                        next;

                    // check if mouse is over a row
                    if (event.pageY >= top && event.pageY < top + rowHeight) {
                        var targetRow = null,
                            targetLoc = null,
                            elementLevel = rowLevel(element);

                        if (event.pageY >= top && event.pageY < top + rowHeight / 3) {
                            targetRow = element;
                            targetLoc = BEFORE;
                        } else if (event.pageY >= top + rowHeight / 3 && event.pageY < top + rowHeight * 2 / 3) {
                            next = element.next();
                            // there's no point in allowing adding children when there are some already
                            // better move the items to the correct place right away
                            if (!next.length || rowLevel(next) <= elementLevel) {
                                targetRow = element;
                                targetLoc = CHILD;
                            }
                        } else if (event.pageY >= top + rowHeight * 2 / 3 && event.pageY < top + rowHeight) {
                            next = element.next();
                            if (!next.length || rowLevel(next) <= elementLevel) {
                                targetRow = element;
                                targetLoc = AFTER;
                            }
                        }

                        if(targetRow) {

                            // Positioning relative to cell containing the link
                            var offset = targetRow.find('th').offset();
                            var left = offset.left
                                + rowLevel(targetRow) * CHILD_PAD
                                + (targetLoc == CHILD ? CHILD_PAD : 0)
                                + 5; // Center of the circle aligns with start of link text (cell padding!)

                            $('#drag-line').css({
                                'width': resultListWidth - left,
                                'left': left,
                                'top': offset.top + (targetLoc == BEFORE ? 0 : rowHeight)
                            }).find('span').text(DraggableMPTTAdmin.messages[targetLoc] || '');

                            // Store the found row and options
                            moveTo.hovering = element;
                            moveTo.relativeTo = targetRow;
                            moveTo.side = targetLoc;

                            return true;
                        }
                    }
                });
            });

            $('body').keydown(function(event) {
                if (event.which == '27') {
                    $('#drag-line').remove();
                    $('#ghost').remove();
                    $('body').removeClass('dragging').enableSelection().unbind('mousemove').unbind('mouseup');
                    event.preventDefault();
                }
            });

            $('body').bind('mouseup', function() {
                if(moveTo.relativeTo) {
                    var cutItem = originalRow.find('.tree-node').data('pk');
                    var pastedOn = moveTo.relativeTo.find('.tree-node').data('pk');

                    // get out early if items are the same
                    if(cutItem != pastedOn) {
                        var isParent = (
                           rowLevel(moveTo.relativeTo.next()) >
                           rowLevel(moveTo.relativeTo));

                        var position = '';

                        // determine position
                        if(moveTo.side == CHILD && !isParent) {
                            position = 'last-child';
                        } else if (moveTo.side == BEFORE) {
                            position = 'left';
                        } else {
                            position = 'right';
                        }

                        $.ajax({
                            complete: function() {
                                window.location.reload();
                            },
                            data: {
                                cmd: 'move_node',
                                position: position,
                                cut_item: cutItem,
                                pasted_on: pastedOn
                            },
                            headers: {
                                'X-CSRFToken': $('input[type=hidden][name=csrfmiddlewaretoken]').val()
                            },
                            method: 'POST'
                        });
                    } else {
                        $('#drag-line').remove();
                        $('#ghost').remove();
                    }
                    $('body').removeClass('dragging').enableSelection().unbind('mousemove').unbind('mouseup');
                }
            });

        });

        return this;
    });

    /* Every time the user expands or collapses a part of the tree, we remember
       the current state of the tree so we can restore it on a reload. */
    function storeCollapsedNodes(nodes) {
        window.localStorage && window.localStorage.setItem(
            DraggableMPTTAdmin.storageName,
            JSON.stringify(nodes)
        );
    }

    function retrieveCollapsedNodes() {
        try {
            return JSON.parse(window.localStorage.getItem(
                DraggableMPTTAdmin.storageName
            ));
        } catch(e) {
            return null;
        }
    }

    function expandOrCollapseNode(item) {
        var show = true;

        if (!item.hasClass('children'))
            return;

        var itemId = item.data('pk');

        if (!isExpandedNode(itemId)) {
            item.removeClass('closed');
            markNodeAsExpanded(itemId);
        } else {
            item.addClass('closed');
            show = false;
            markNodeAsCollapsed(itemId);
        }

        storeCollapsedNodes(DraggableMPTTAdmin.collapsedNodes);

        doToggle(itemId, show);
    }

    function collapseTree() {
        var rlist = $("#result_list");
        rlist.hide();
        $('tbody tr', rlist).each(function(i, el) {
            var marker = $('.tree-node', el);
            if (marker.hasClass('children')) {
                var itemId = marker.data('pk');
                doToggle(itemId, false);
                marker.addClass('closed');
                markNodeAsCollapsed(itemId);
            }
        });
        storeCollapsedNodes(DraggableMPTTAdmin.collapsedNodes);
        rlist.show();
        return false;
    }

    function expandTree() {
        var rlist = $("#result_list");
        rlist.hide();
        $('tbody tr', rlist).each(function(i, el) {
            var marker = $('.tree-node', el);
            if (marker.hasClass('children')) {
                var itemId = $('.tree-node', el).data('pk');
                doToggle(itemId, true);
                marker.removeClass('closed');
                markNodeAsExpanded(itemId);
            }
        });
        storeCollapsedNodes([]);
        rlist.show();
        return false;
    }

    var changelistTab = function(elem, event, direction) {
        event.preventDefault();
        elem = $(elem);
        var ne = (direction > 0) ? elem.nextAll(':visible:first') : elem.prevAll(':visible:first');
        if(ne) {
            elem.attr('tabindex', -1);
            ne.attr('tabindex', '0');
            ne.focus();
        }
    };

    function keyboardNavigationHandler(event) {
        // On form element? Ignore.
        if (/textarea|select|input/i.test(event.target.nodeName))
            return;

        // console.log('keydown', this, event.keyCode);
        switch (event.keyCode) {
            case 40: // down
                changelistTab(this, event, 1);
                break;
            case 38: // up
                changelistTab(this, event, -1);
                break;
            case 37: // left
            case 39: // right
                expandOrCollapseNode($(this).find('.tree-node'));
                break;
            case 13: // return
                document.location = $('a', this).attr('href');
                break;
            default:
                break;
        }
    }

    function addObjectTool(title, handler) {
        var $a = $('<a href/>');
        $a.click(handler);
        $a.text(title);
        $a.prependTo('.object-tools').wrap('<li>');
    }

    // Some old browsers do not support JSON.parse (the only thing we require)
    var jsonParse = JSON.parse || function jsonParse(sJSON) { return eval('(' + sJSON + ')'); };

    DraggableMPTTAdmin = jsonParse(
        document.getElementById('draggable-admin-context').getAttribute('data-context'));

    addObjectTool(DraggableMPTTAdmin.messages.collapseTree, collapseTree);
    addObjectTool(DraggableMPTTAdmin.messages.expandTree, expandTree);

    // fire!
    var rlist = $("#result_list"),
        rlist_tbody = rlist.find('tbody');

    if ($('tbody tr', rlist).length > 1) {
        rlist_tbody.feinTree();

        rlist.find('.tree-node').on('click', function(event) {
            event.preventDefault();
            event.stopPropagation();

            expandOrCollapseNode($(this));
        });

        /* Enable focussing, put focus on first result, add handler for keyboard navigation */
        $('tr', rlist).attr('tabindex', -1);
        $('tbody tr:first', rlist).attr('tabindex', 0).focus();
        $('tr', rlist).keydown(keyboardNavigationHandler);

        DraggableMPTTAdmin.collapsedNodes = [];
        var storedNodes = retrieveCollapsedNodes();

        if (storedNodes) {
            for(var i=0; i<storedNodes.length; i++) {
                expandOrCollapseNode(treeNode(storedNodes[i]));
            }
        } else {
            if (!DraggableMPTTAdmin.expandTreeByDefault) {
                collapseTree();
            }
        }
    }

});
