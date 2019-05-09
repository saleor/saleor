function generateCenterpointWidget(){
    // Find all images with the class 'sizedimage-preview'
    var crops = document.getElementsByClassName('sizedimage-preview')
    // Iterate through those images
    for (var x=0; x<crops.length; x++){(function(){
        var crop = crops[x],
            point_stage = document.getElementById(crop.getAttribute('data-point_stage_id')),
            hidden_field = document.getElementById(crop.getAttribute('data-hidden_field_id')),
            point = document.getElementById(crop.getAttribute('data-ppoi_id')),
            current_ppoi = hidden_field.value.split('x')
        // Sizing the ppoi stage to the size the sized image
        point_stage.width = crop.clientWidth
        point_stage.height = crop.clientHeight
        point_stage.style.width = crop.clientWidth + 'px'
        point_stage.style.height = crop.clientHeight + 'px'
        // Assigning the click handler
        point_stage.onclick = cropClick
        // Setting the ppoi to the current value of `hidden_field`
        point.style.left = ((point_stage.width * parseFloat(current_ppoi[0])) - (point.offsetWidth / 2)) + 'px'
        point.style.top = ((point_stage.height * parseFloat(current_ppoi[1])) - (point.offsetHeight / 2)) + 'px'
    })()}

    function cropClick (e) {
        var x = e.offsetX==undefined?e.layerX:e.offsetX,
            y = e.offsetY==undefined?e.layerY:e.offsetY,
            x_coord = parseFloat(x / this.width).toFixed(2),
            y_coord = parseFloat(y / this.height).toFixed(2),
            cropped_image = document.getElementById(this.getAttribute('data-image_preview_id')),
            hidden_input = document.getElementById(cropped_image.getAttribute('data-hidden_field_id')),
            point = document.getElementById(cropped_image.getAttribute('data-ppoi_id')),
            val = x_coord + 'x' + y_coord
        hidden_input.value = val
        point.style.top = (y - (point.offsetWidth / 2)) + 'px'
        point.style.left = (x - (point.offsetHeight / 2)) + 'px'
    }
}

window.addEventListener("load", generateCenterpointWidget);
