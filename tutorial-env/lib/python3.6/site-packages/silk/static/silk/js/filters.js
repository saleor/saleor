
function configureResizingInputs() {
    var $inputs = $('.resizing-input');

    function resizeForText(text) {
        var $this = $(this);
        if (!text.trim()) {
            text = $this.attr('placeholder').trim();
        }
        var $span = $this.parent().find('span');
        $span.text(text);
        var $inputSize = $span.width();
        $this.css("width", $inputSize);
    }

    $inputs.find('input').keypress(function (e) {
        if (e.which && e.charCode) {
            var c = String.fromCharCode(e.keyCode | e.charCode);
            var $this = $(this);
            resizeForText.call($this, $this.val() + c);
        }
    });

    $inputs.find('input').keyup(function (e) { // Backspace event only fires for keyup
        if (e.keyCode === 8 || e.keyCode === 46) {
            resizeForText.call($(this), $(this).val());
        }
    });

    $inputs.find('input').each(function () {
        var $this = $(this);
        resizeForText.call($this, $this.val())
    });


    $('.resizing-input .datetimepicker').datetimepicker({
        step: 10,
        onChangeDateTime: function (dp, $input) {
            resizeForText.call($input, $input.val())
        }
    });

}

/**
 * Entry point for filter initialisation.
 */
function initFilters() {
    configureResizingInputs();
}