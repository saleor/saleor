const $seoTitle = $('#seo_title');

const $nameId = $seoTitle.data('bind');
const $name = $(`#${$nameId}`);

const $seoDescription = $('#seo_description');
const $descriptionMaterialize = $seoDescription.data('materialize');
if ($descriptionMaterialize) {
  var $description = $(`.materialize-textarea[name='${$descriptionMaterialize}']`);
} else {
  const $descriptionId = $seoDescription.data('bind');
  var $description = $(`#${$descriptionId}`);
}

const $googleTitlePreview = $('#google-preview-title');
const $googleDescriptionPreview = $('#google-preview-description');
const $preview = $('.preview');
const $previewErrors = $('#preview-error');

const watchedEvents = 'input propertychange cut paste copy change delete';

function checkForErrors() {
  const $descriptionText = $googleDescriptionPreview.text() || $googleDescriptionPreview.val();
  const $titleText = $googleTitlePreview.text();
  if ($descriptionText && $titleText) {
    $preview.show();
    $previewErrors.hide();
  } else if (!$descriptionText && !$titleText) {
    $preview.hide();
    $previewErrors.text(gettext('title and description missing'));
    $previewErrors.show();

    // title and descriptions missing
  } else if (!$descriptionText) {
    $preview.hide();
    $previewErrors.show();
    $previewErrors.text(gettext('description missing'));

    // description missing
  } else if (!$titleText) {
    // title missing
    $preview.hide();
    $previewErrors.show();
    $previewErrors.text(gettext('title missing'));
  }
}

function truncate(text, seoField) {
  const $fieldMaxLength = seoField.prop('maxLength');
  if ($fieldMaxLength === -1) {
    // console.log('Field maxlength is not defined');
    return text;
  }
  return text.substring(text, $fieldMaxLength);
}

function updatePlaceholderOnInput(field, seoField, previewField) {
  field.on(watchedEvents, (e) => {
    const $target = $(e.currentTarget);
    const $placeholderText = $target.val();
    console.log($placeholderText);
    seoField.attr('placeholder', truncate($placeholderText, seoField));
    const $seoText = seoField.val();
    console.log($seoText);
    if (!$seoText) {
      previewField.text(truncate($placeholderText, seoField));
    } else {
      previewField.text(truncate($seoText, seoField));
    }
    checkForErrors();
  });
}

function updatePreviewOnInput(seoField, previewField) {
  seoField.on(watchedEvents, (e) => {
    const $target = $(e.currentTarget);
    const $currentText = $target.val();
    if ($currentText) {
      previewField.text(truncate($currentText, seoField));
    } else {
      const $placeholderValue = seoField.attr('placeholder');
      previewField.text(truncate($placeholderValue, seoField));
    }
    checkForErrors();
  });
}
checkForErrors();
updatePlaceholderOnInput($name, $seoTitle, $googleTitlePreview);
updatePlaceholderOnInput($description, $seoDescription, $googleDescriptionPreview);
updatePreviewOnInput($seoTitle, $googleTitlePreview);
updatePreviewOnInput($seoDescription, $googleDescriptionPreview);
