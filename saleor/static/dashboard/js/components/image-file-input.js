function onImageSelect(event) {
  const self = event.target || event;

  if (self.files.length > 0) {
    const targetElement = document.getElementById(
      self.attributes['data-image-target-id'].value);

    const reader = new FileReader();
    reader.onload = function (e) {
      targetElement.src = e.target.result;
    };

    reader.readAsDataURL(self.files[0]);
  }
}

function DropAreaHoverHandler(isHover) {
  function onEvent(event) {
    const self = event.currentTarget;
    $(self).toggleClass('hover', isHover);
  }
  return onEvent;
}

$('[data-handle-image-input]').each(function (i, element) {
  element.addEventListener('change', onImageSelect);
  onImageSelect(element);
});

const dropAreaHoverEvent = DropAreaHoverHandler(true);
const dropAreaHoverExitedEvent = DropAreaHoverHandler(false);

$('.image-dropzone').each(function (i, element) {
  element = $(element);
  element.on('mouseenter', dropAreaHoverEvent);
  element.on('dragenter', dropAreaHoverEvent);
  element.on('mouseleave', dropAreaHoverExitedEvent);
  element.on('dragleave', dropAreaHoverExitedEvent);
});
