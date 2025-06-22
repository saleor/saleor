# Telegram Email Change Confirm Mutation Fix Summary

## 🐛 Issue Description

Users encountered the following errors when using the `telegramEmailChangeConfirm` mutation:

1. **Parameter Error**: `Unknown argument "oldEmail" on field "telegramEmailChangeConfirm"`
2. **Parameter Error**: `Unknown argument "newEmail" on field "telegramEmailChangeConfirm"`
3. **Field Error**: `Cannot query field "success" on type "TelegramEmailChangeConfirm"`

## ✅ Fix Content

### 1. Add Required Parameters

Added `old_email` and `new_email` parameters to the `TelegramEmailChangeConfirm` mutation:

```python
class Arguments:
    init_data_raw = graphene.String(
        required=True,
        description="Telegram WebApp initDataRaw string"
    )
    verification_code = graphene.String(
        required=True,
        description="Verification code received via email"
    )
    old_email = graphene.String(
        required=True,
        description="Current email address (telegram_xxx@telegram.local format)"
    )
    new_email = graphene.String(
        required=True,
        description="New email address to change to"
    )
```

### 2. Add Return Fields

Added the `success` return field:

```python
user = graphene.Field(User, description="User with updated email")
success = graphene.Boolean(description="Whether the email change was successful")
token = graphene.String(description="JWT token for the user")
```

### 3. Enhanced Parameter Validation

Implemented multi-layer parameter validation:

- **Old Email Format Validation**: Must be in `telegram_{id}@telegram.local` format
- **New Email Format Validation**: Must be a valid email format and cannot be Telegram format
- **User Email Consistency**: The provided old email must match the user's current email
- **Redis Data Consistency**: The provided parameters must match the request data stored in Redis

### 4. Improved Error Handling

Enhanced error handling mechanism to provide more detailed error information:

```python
# Parameter validation error
raise ValidationError({
    'old_email': ValidationError(
        'Invalid old email format',
        code=AccountErrorCode.INVALID.value
    )
})

# Data consistency error
raise ValidationError({
    'old_email': ValidationError(
        'Provided old email does not match the stored request',
        code=AccountErrorCode.INVALID.value
    )
})
```

## 📋 Usage Method

### GraphQL Mutation Structure

```graphql
mutation TelegramEmailChangeConfirm(
  $initDataRaw: String!
  $verificationCode: String!
  $oldEmail: String!
  $newEmail: String!
) {
  telegramEmailChangeConfirm(
    initDataRaw: $initDataRaw
    verificationCode: $verificationCode
    oldEmail: $oldEmail
    newEmail: $newEmail
  ) {
    user {
      email
      firstName
      lastName
    }
    success
    token
    errors {
      field
      message
      code
    }
  }
}
```

### Request Parameter Example

```json
{
  "initDataRaw": "user%3D%257B%2522id%2522%253A5861990984%252C%2522first_name%2522%253A%2522King%2522%252C%2522last_name%2522%253A%2522%2522%252C%2522username%2522%253A%2522Svenlai666%2522%252C%2522language_code%2522%253A%2522zh-hans%2522%252C%2522allows_write_to_pm%2522%253Atrue%252C%2522photo_url%2522%253A%2522https%253A%255C%252F%255C%252Ft.me%255C%252Fi%255C%252Fuserpic%255C%252F320%255C%252FfOso4OMYHXqI0CdCO2hxaqi5A23cXtUBjFLnUoRJa_aPy1E8DABF_Hm179IT0QOn.svg%2522%257D%26chat_instance%3D3930809717662463213%26chat_type%3Dprivate%26auth_date%3D1745999001%26signature%3DCVuFy8jWC8PNwkWdbA7tPueIbNqkUNxtillFjZQGL2yY47BhtAhh6QGqc3UwLwq9QYG6eMBSf-pcNibA49YUCA%26hash%3D5fb2ea078b8265c57271590e5a41f7a050f9892c25defd98fb7b380e3305d228&tgWebAppVersion=8.0&tgWebAppPlatform=macos&tgWebAppThemeParams=%7B%22secondary_bg_color%22%3A%22%23131415%22%2C%22subtitle_text_color%22%3A%22%23b1c3d5%22%2C%22text_color%22%3A%22%23ffffff%22%2C%22section_header_text_color%22%3A%22%23b1c3d5%22%2C%22destructive_text_color%22%3A%22%23ef5b5b%22%2C%22bottom_bar_bg_color%22%3A%22%23213040%22%2C%22section_bg_color%22%3A%22%2318222d%22%2C%22button_text_color%22%3A%22%23ffffff%22%2C%22accent_text_color%22%3A%22%232ea6ff%22%2C%22button_color%22%3A%22%232ea6ff%22%2C%22link_color%22%3A%22%2362bcf9%22%2C%22bg_color%22%3A%22%2318222d%22%2C%22hint_color%22%3A%22%23b1c3d5%22%2C%22header_bg_color%22%3A%22%23131415%22%2C%22section_separator_color%22%3A%22%23213040%22%7D",
  "verificationCode": "507103",
  "oldEmail": "telegram_5861990984@telegram.local",
  "newEmail": "88888888@qq.com"
}
```

### Success Response Example

```json
{
  "data": {
    "telegramEmailChangeConfirm": {
      "user": {
        "email": "88888888@qq.com",
        "firstName": "King",
        "lastName": ""
      },
      "success": true,
      "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "errors": []
    }
  }
}
```

### Error Response Example

```json
{
  "errors": [
    {
      "message": "Invalid verification code",
      "locations": [
        {
          "line": 10,
          "column": 5
        }
      ],
      "extensions": {
        "exception": {
          "code": "GraphQLError"
        }
      }
    }
  ]
}
```

## 🔒 Security Features

### 1. Multi-layer Validation Mechanism

- **Telegram Data Validation**: Verify the authenticity of `initDataRaw`
- **User Identity Authentication**: Find users through `telegram_id`
- **Parameter Format Validation**: Validate email format and verification code format
- **Data Consistency Validation**: Ensure provided parameters match Redis stored data
- **Verification Code Validation**: Verify the correctness of email verification codes
- **Expiration Time Validation**: 10-minute validity period for verification codes

### 2. Redis Data Association

Verification code data stored in Redis includes complete association information:

```python
cache_data = {
    'telegram_id': telegram_id,
    'user_id': user.pk,
    'old_email': old_email,
    'new_email': new_email,
    'verification_code': verification_code,
    'created_at': created_at.isoformat(),
    'expires_at': expires_at.isoformat()
}
```

### 3. Double-check Mechanism

- **Parameter Validation**: Validate the format of provided `oldEmail` and `newEmail`
- **Redis Validation**: Verify consistency between provided parameters and Redis stored data
- **Database Validation**: Finally verify if the new email is already used by other users

## 🧪 Test Verification

### Test Scripts

Created two test scripts to verify the fix:

1. **`test_telegram_email_change_confirm_fixed.py`**: Comprehensive testing of mutation functionality
2. **`test_mutation_call.py`**: Verify GraphQL call structure

### Test Results

All tests passed:

```
📊 Test Summary:
   mutation parameter definition: ✅ Passed
   mutation return fields: ✅ Passed
   parameter validation logic: ✅ Passed
   Redis data consistency: ✅ Passed
   GraphQL mutation structure: ✅ Passed
   error handling: ✅ Passed
   mutation structure: ✅ Passed
   expected response: ✅ Passed
   error response: ✅ Passed
   parameter validation: ✅ Passed

Total: 10/10 tests passed
```

## 📝 Modified Files

1. **`saleor/graphql/account/mutations/authentication/telegram_email_change_confirm.py`**
   - Added `old_email` and `new_email` parameters
   - Added `success` return field
   - Enhanced parameter validation logic
   - Improved error handling mechanism

## 🚀 Deployment Instructions

1. **Restart Service**: After modification, restart the Saleor service to load the new mutation
2. **Environment Variables**: Ensure `EMAIL_URL` and `REDIS_URL` are configured correctly
3. **Test Verification**: Use the provided test scripts to verify functionality

## ✅ Fix Completed

Now the `telegramEmailChangeConfirm` mutation supports:

- ✅ Accept `oldEmail` and `newEmail` parameters
- ✅ Return `success` field
- ✅ Complete parameter validation
- ✅ Secure email change process
- ✅ Detailed error handling
- ✅ Redis data consistency validation
