import "./scss/index.scss";

import * as React from "react";

import { Button, Form, TextField } from "../..";
import { maybe } from "../../../core/utils";
import { TypedCustomerRegisterMutation } from "./queries";
import { RegisterCutomer } from "./types/RegisterCutomer";

import { AlertManager, useAlert } from "react-alert";

const showSuccessNotification = (
  data: RegisterCutomer,
  hide: () => void,
  alert: AlertManager
) => {
  const successful = maybe(() => !data.customerRegister.errors.length);

  if (successful) {
    hide();
    alert.show(
      {
        title: "New user has been created",
      },
      { type: "success" }
    );
  }
};

const RegisterForm: React.FC<{ hide: () => void }> = ({ hide }) => {
  const alert = useAlert();
  return (
    <TypedCustomerRegisterMutation
      onCompleted={data => showSuccessNotification(data, hide, alert)}
    >
      {(registerCustomer, { loading, data }) => {
        return (
          <Form
            errors={maybe(() => data.customerRegister.errors, [])}
            onSubmit={(event, { email, password }) => {
              event.preventDefault();
              registerCustomer({ variables: { email, password } });
            }}
          >
            <TextField
              name="email"
              autoComplete="email"
              label="Email Address"
              type="email"
              required
            />
            <TextField
              name="password"
              autoComplete="password"
              label="Password"
              type="password"
              required
            />
            <div className="login__content__button">
              <Button type="submit" {...loading && { disabled: true }}>
                {loading ? "Loading" : "Register"}
              </Button>
            </div>
          </Form>
        );
      }}
    </TypedCustomerRegisterMutation>
  );
};

export default RegisterForm;
