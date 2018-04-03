function onImageSelect(self) {
  self = self.target || self;

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

$('[data-handle-image-input]').each(function (i, element) {
  element.addEventListener('change', onImageSelect);
  onImageSelect(element);
});
