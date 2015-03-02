$.fn.addDeleteButtons = function() {
    this.find('input[type="number"]').each(function(){
        var icon = $('<i>').addClass('glyphicon glyphicon-trash');
        var button = $('<button>').addClass('btn btn-danger delete-button').html(icon);
        var container = $('<div>').addClass('input-group-btn').html(button);
        $(this).after(container);
        $(this).parent().addClass('input-group');
    });
    this.find('.delete-button').click(function(){
        $(this).parents('tr').find('input[type="number"]').val('0');
    })
};
