export default $(document).ready(e => {
    let $formButton = $('form:has(.btn-only-once)');
    if (!$formButton)
        return;
    $formButton.submit(function(e){
        let $button = $('.btn-only-once', $(this));
        $button.prop('disabled', true);
    })
});
  