import "./scss/index.scss";

import classNames from "classnames";
import * as React from "react";

import { Form, Select, TextField } from "..";

import { ShopContext } from "../ShopProvider/context";
import { FormAddressType, IShippingNewAddressFormProps } from "./types";
import { getFormData } from "./utils";

export const AddNewShippingAddressForm: React.FC<
  IShippingNewAddressFormProps
> = ({ data, errors, onSubmit, children, type }) => (
  <div className="address-form">
    <ShopContext.Consumer>
      {({ countries, geolocalization, defaultCountry }) => (
        <Form<FormAddressType>
          id="new-address-form"
          errors={errors}
          onSubmit={(evt, data) => {
            evt.preventDefault();
            onSubmit(data);
          }}
          data={getFormData(geolocalization, defaultCountry, data)}
        >
          {children}

          <div className="address-form__grid address-form__grid--modal">
            <TextField
              label="First Name"
              type="given-name"
              name="firstName"
              autoComplete="given-name"
              required
            />
            <TextField
              label="Last Name"
              type="family-name"
              name="lastName"
              autoComplete="family-name"
              required
            />
          </div>
          <TextField
            label="Street Name"
            type="address-line1"
            name="streetAddress1"
            autoComplete="address-line1"
            required
          />
          <TextField
            label="Company name (optional)"
            type="organization"
            name="companyName"
            autoComplete="organization"
          />
          <div className="address-form__grid address-form__grid--modal">
            <TextField
              label="ZIP Code"
              type="postal-code"
              name="postalCode"
              autoComplete="postal-code"
              required
            />
            <TextField
              label="City"
              type="city"
              name="city"
              autoComplete="address-level2"
              required
            />
          </div>
          <div className="address-form__grid address-form__grid--modal">
            <TextField
              label="State/Province"
              type="state"
              name="countryArea"
              autoComplete="address-level1"
            />
            <Select
              label="Country"
              name="country"
              options={countries.map(country => ({
                label: country.country,
                value: country.code,
              }))}
              autoComplete="country"
            />
          </div>
          <div
            className={classNames(
              "address-form__grid address-form__grid--modal",
              {
                "address-form__grid--full": type === "billing",
              }
            )}
          >
            {type === "shipping" && (
              <TextField
                label="Email Address"
                type="email"
                autoComplete="email"
                name="email"
                required
              />
            )}

            <TextField
              label="Phone number"
              type="tel"
              name="phone"
              autoComplete="tel"
              required
            />
          </div>
          <label className="checkbox checkbox__bottom">
            <input name="asNew" type="checkbox" />
            <span>{`Use this address as new ${type} address`}</span>
          </label>
        </Form>
      )}
    </ShopContext.Consumer>
  </div>
);

export default AddNewShippingAddressForm;
