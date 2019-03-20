import Button from "@material-ui/core/Button";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import TextField from "@material-ui/core/TextField";
import Typography from "@material-ui/core/Typography";
import * as React from "react";
import SVG from "react-inlinesvg";

import * as saleorLogo from "../../../../images/logo-document.svg";
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

const styles = (theme: Theme) =>
  createStyles({
    buttonContainer: {
      display: "flex",
      justifyContent: "space-between"
    },
    link: {
      color: theme.palette.primary.main,
      cursor: "pointer",
      textAlign: "center"
    },
    loginButton: {
      width: 140
    },
    logo: {
      "& svg": {
        display: "block",
        height: 40,
        marginBottom: theme.spacing.unit * 4
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
      display: "grid",
      gridTemplateColumns: "424px 1fr"
    },
    sidebar: {
      background: theme.palette.background.paper,
      display: "flex",
      flexDirection: "column",
      height: "100vh",
      justifyContent: "center",
      padding: theme.spacing.unit * 6,
      width: "100%"
    }
  });

export interface LoginCardProps extends WithStyles<typeof styles> {
  error: boolean;
  disableLoginButton: boolean;
  onPasswordRecovery: () => void;
  onSubmit?(event: FormData);
}

const LoginCard = withStyles(styles, { name: "LoginCard" })(
  ({ classes, error, disableLoginButton, onSubmit }: LoginCardProps) => {
    return (
      <Form
        initial={{ email: "", password: "", rememberMe: false }}
        onSubmit={onSubmit}
      >
        {({ change: handleChange, data, submit: handleSubmit }) => (
          <div className={classes.root}>
            <div className={classes.sidebar}>
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
              <div className={classes.buttonContainer}>
                <ControlledCheckbox
                  checked={data.rememberMe}
                  label={i18n.t("Remember me")}
                  name="rememberMe"
                  onChange={handleChange}
                />
                <FormSpacer />
                <Button
                  className={classes.loginButton}
                  color="primary"
                  disabled={disableLoginButton}
                  variant="contained"
                  onClick={handleSubmit}
                  type="submit"
                >
                  {i18n.t("Login")}
                </Button>
              </div>
              {/* <FormSpacer />
                <Typography className={classes.link}>
                  {i18n.t("Reset your password")}
                </Typography> */}
            </div>
            {/* TODO: Add parrot */}
            <div>placeholder</div>
          </div>
        )}
      </Form>
    );
  }
);
LoginCard.displayName = "LoginCard";
export default LoginCard;
