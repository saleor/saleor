import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import { withStyles } from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import * as React from "react";
import SVG from "react-inlinesvg";

import * as saleorLogo from "../../../../images/logo-document.svg";
import Container from "../../../components/Container";
import { ControlledCheckbox } from "../../../components/ControlledCheckbox";
import Form from "../../../components/Form";
import { FormSpacer } from "../../../components/FormSpacer";
import i18n from "../../../i18n";

export interface FormData {
  email: string;
  loading: boolean;
  password: string;
  rememberMe: boolean;
}
export interface LoginCardProps {
  error: boolean;
  disableLoginButton: boolean;
  onPasswordRecovery: () => void;
  onSubmit?(event: FormData);
}

const decorate = withStyles(theme => ({
  card: {
    [theme.breakpoints.down("xs")]: {
      boxShadow: "none" as "none",
      padding: theme.spacing.unit * 4,
      width: "100%"
    },
    padding: `${theme.spacing.unit * 10.5}px ${theme.spacing.unit * 17}px`,
    width: "100%"
  },
  link: {
    color: theme.palette.primary.main,
    cursor: "pointer" as "pointer",
    textAlign: "center" as "center"
  },
  loginButton: {
    width: "100%"
  },
  logo: {
    "& svg": {
      display: "block" as "block",
      margin: `0 auto ${theme.spacing.unit * 7}px`
    }
  },
  panel: {
    "& span": {
      color: theme.palette.error.contrastText
    },
    background: theme.palette.error.main,
    borderRadius: theme.spacing.unit,
    marginBottom: theme.spacing.unit * 3,
    padding: theme.spacing.unit * 1.5
  },
  root: {
    [theme.breakpoints.down("xs")]: {
      background: "#fff",
      boxShadow: "none" as "none"
    },
    alignItems: "center" as "center",
    display: "flex",
    height: "100vh"
  }
}));
const LoginCard = decorate<LoginCardProps>(
  ({ classes, error, disableLoginButton, onSubmit }) => {
    return (
      <Form
        initial={{ email: "", password: "", rememberMe: false }}
        onSubmit={onSubmit}
      >
        {({ change: handleChange, data, submit: handleSubmit }) => (
          <Container className={classes.root} width="sm">
            <Card className={classes.card}>
              <SVG className={classes.logo} src={saleorLogo} />
              {error && (
                <div className={classes.panel}>
                  <Typography
                    variant="caption"
                    dangerouslySetInnerHTML={{
                      __html: i18n.t(
                        "Sorry, your username and/or password are incorrect. <br />Please try again."
                      )
                    }}
                  />
                </div>
              )}
              <TextField
                autoFocus
                fullWidth
                autoComplete="username"
                label={i18n.t("Email", { context: "form" })}
                name="email"
                onChange={handleChange}
                value={data.email}
              />
              <FormSpacer />
              <TextField
                fullWidth
                autoComplete="current-password"
                label={i18n.t("Password")}
                name="password"
                onChange={handleChange}
                type="password"
                value={data.password}
              />
              <FormSpacer />
              <ControlledCheckbox
                checked={data.rememberMe}
                label={i18n.t("Remember me")}
                name="rememberMe"
                onChange={handleChange}
              />
              <FormSpacer />
              <Button
                className={classes.loginButton}
                color="secondary"
                disabled={disableLoginButton}
                variant="raised"
                onClick={handleSubmit}
                type="submit"
              >
                {i18n.t("Login")}
              </Button>
              {/* <FormSpacer />
                <Typography className={classes.link}>
                  {i18n.t("Reset your password")}
                </Typography> */}
            </Card>
          </Container>
        )}
      </Form>
    );
  }
);
LoginCard.displayName = "LoginCard";
export default LoginCard;
