const $seoTitle = $('#id_seo_title');

const $nameId = $seoTitle.data('bind');
const $name = $(`#${$nameId}`);

const $seoDescription = $('#id_seo_description');
const $descriptionMaterialize = $seoDescription.data('materialize');

let $description = '';
const $descriptionId = $seoDescription.data('bind');
if ($descriptionMaterialize) {
  const $descriptions = $(`.materialize-textarea[name='${$descriptionMaterialize}']`);
  // They're two textareas from Medium editor, first one contains HTML-free text
  $description = $descriptions.not($descriptionId).first();
} else {
  if ($descriptionId) {
    $description = $(`#${$descriptionId}`);
  }
}

const $googleTitlePreview = $('#google-preview-title');
const $googleDescriptionPreview = $('#google-preview-description');
const $preview = $('#google-preview');

const watchedEvents = 'input propertychange cut paste copy change';

function setPlaceholderAndPreview(field, seoField, previewField) {
  const $text = field.text() || field.val();
  const $placeholderText = truncate($text, seoField);
  seoField.attr('placeholder', $placeholderText);
  previewField.text(seoField.val() || $placeholderText);
}

function updateCharsCount(seoField) {
  const $fieldId = seoField.attr('id');
  const $charCount = $(`span[data-bind=${$fieldId}]`);
  let $fieldLength = seoField.val().length || seoField.text().length;
  if (!$fieldLength && seoField.attr('placeholder')) {
    $fieldLength = seoField.attr('placeholder').length;
  }
  const $minRecommendedLength = seoField.data('min-recommended-length');
  const $charCountWrapper = $charCount.parent();
  if ($fieldLength < $minRecommendedLength) {
    $charCountWrapper.addClass('orange-text');
    $charCountWrapper.removeClass('green-text');
    $charCountWrapper.attr('title', gettext('Your input might be a little too short, think of something more descriptive'));
  } else {
    $charCountWrapper.removeClass('orange-text');
    $charCountWrapper.addClass('green-text');
    $charCountWrapper.attr('title', gettext('Your input fits between the recommended lengths'));
  }
  $charCount.text($fieldLength);
}

function checkForErrors() {
  const $descriptionText = $googleDescriptionPreview.text();
  const $titleText = $googleTitlePreview.text();
  if ($descriptionText && $titleText) {
    $preview.show();
  } else {
    $preview.hide();
  }
}

function truncate(text, seoField) {
  const $fieldMaxLength = seoField.prop('maxLength');
  if (text && text.length > $fieldMaxLength) {
    return text.substring(text, $fieldMaxLength);
  }
  return text;
}

function updatePlaceholderOnInput(field, seoField, previewField) {
  field.on(watchedEvents, (e) => {
    const $target = $(e.currentTarget);
    const $placeholderText = $target.val() || $target.text();
    seoField.attr('placeholder', truncate($placeholderText, seoField));
    const $seoText = seoField.val();
    if (!$seoText) {
      previewField.text(truncate($placeholderText, seoField));
    }
    checkForErrors();
    updateCharsCount(seoField);
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
    updateCharsCount(seoField);
  });
}

if ($seoTitle.length) {
  if ($name) {
    setPlaceholderAndPreview($name, $seoTitle, $googleTitlePreview);
    updatePlaceholderOnInput($name, $seoTitle, $googleTitlePreview);
  }
  updatePreviewOnInput($seoTitle, $googleTitlePreview);
  updateCharsCount($seoTitle);
}
if ($seoDescription.length) {
  if ($description) {
    setPlaceholderAndPreview($description, $seoDescription, $googleDescriptionPreview);
    updatePlaceholderOnInput($description, $seoDescription, $googleDescriptionPreview);
  }
  updatePreviewOnInput($seoDescription, $googleDescriptionPreview);
  updateCharsCount($seoDescription);
}
checkForErrors();
