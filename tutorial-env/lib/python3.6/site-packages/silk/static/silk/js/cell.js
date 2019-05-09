function configureSpanFontColors(selector, okValue, badValue) {
    selector.each(function () {
        var val = parseFloat($(this).text());
        if (val < okValue) {
            $(this).addClass('very-good-font-color');
        }
        else if (val < badValue) {
            $(this).addClass('ok-font-color');
        }
        else {
            $(this).addClass('very-bad-font-color');
        }
    });
}

function configureFontColors() {
    configureSpanFontColors($('.time-taken-div .numeric'), 200, 500);
    configureSpanFontColors($('.time-taken-queries-div .numeric'), 50, 200);
    configureSpanFontColors($('.num-queries-div .numeric'), 10, 50);
}

$(document).ready(function () {
    configureFontColors();
});