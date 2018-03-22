import Button from "material-ui/Button";
import { CardContent } from "material-ui/Card";
import CheckBox from "material-ui/Checkbox";
import Grid from "material-ui/Grid";
import { withStyles, WithStyles } from "material-ui/styles";
import TextField from "material-ui/TextField";
import Toolbar from "material-ui/Toolbar";
import Typography from "material-ui/Typography";
import * as React from "react";

import ControlledCheckbox from "../../components/ControlledCheckbox";
import FormSpacer from "../../components/FormSpacer";
import RichTextEditor from "../../components/RichTextEditor";
import i18n from "../../i18n";
import { pageDetailsQuery, TypedPageDetailsQuery } from "../queries";

interface PageUpdateFormComponentState {
  availableOn: string;
  content: string;
  isVisible: boolean;
  slug: string;
  title: string;
}

interface PageUpdateFormComponentProps {
  created?: string;
  errors?: Array<{ field: string; message: string }>;
  formInitialValues?: PageUpdateFormComponentState;
  handleSubmit(data: any);
}

interface CombinedErrorsType {
  availableOn: string;
  content: string;
  slug: string;
  title: string;
}

const decorate = withStyles(theme => ({
  addHelperTextPadding: {
    [theme.breakpoints.up("md")]: {
      paddingBottom: theme.spacing.unit * 2.5
    }
  },
  cardActions: {
    flexDirection: "row-reverse" as "row-reverse"
  }
}));

export const PageUpdateFormComponent = decorate(
  class PageUpdateFormUnstyledComponent extends React.Component<
    PageUpdateFormComponentProps &
      WithStyles<"cardActions" | "addHelperTextPadding">,
    PageUpdateFormComponentState
  > {
    static defaultState = {
      availableOn: "",
      content: "",
      isVisible: false,
      slug: "",
      title: ""
    };

    constructor(props) {
      super(props);
      this.state = {
        ...PageUpdateFormUnstyledComponent.defaultState,
        ...props.formInitialValues
      };
    }

    handleChange = event => {
      this.setState({ [event.target.name]: event.target.value });
    };

    render() {
      const {
        classes,
        created,
        errors,
        formInitialValues,
        handleSubmit
      } = this.props;
      const combinedErrors = errors
        ? (errors.reduce((prev, curr) => {
            prev[curr.field] = curr.message;
            return prev;
          }, {}) as CombinedErrorsType)
        : undefined;
      return (
        <>
          <CardContent>
            <Grid container spacing={16}>
              <Grid item xs={12} md={9}>
                <TextField
                  name="title"
                  label={i18n.t("Title", { context: "object" })}
                  defaultValue={this.state.title}
                  onChange={this.handleChange}
                  className={
                    (errors ? !combinedErrors.title : true)
                      ? classes.addHelperTextPadding
                      : ""
                  }
                  helperText={
                    combinedErrors && combinedErrors.title
                      ? combinedErrors.title
                      : ""
                  }
                  fullWidth
                />
                <FormSpacer />
                <RichTextEditor
                  defaultValue={this.state.content}
                  name="content"
                  label={i18n.t("Content", { context: "object" })}
                  helperText={
                    combinedErrors && combinedErrors.content
                      ? combinedErrors.content
                      : i18n.t("Select text to enable text-formatting tools.", {
                          context: "object"
                        })
                  }
                  onChange={this.handleChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <TextField
                  name="slug"
                  label={i18n.t("Slug", { context: "object" })}
                  defaultValue={this.state.slug}
                  helperText={
                    combinedErrors && combinedErrors.slug
                      ? combinedErrors.slug
                      : i18n.t("Slug is being used to create page URL", {
                          context: "object"
                        })
                  }
                  onChange={this.handleChange}
                  fullWidth
                />
                <FormSpacer />
                <TextField
                  name="availableOn"
                  label={i18n.t("Available on", { context: "label" })}
                  type="date"
                  defaultValue={this.state.availableOn}
                  onChange={this.handleChange}
                  InputLabelProps={{
                    shrink: true
                  }}
                  helperText={
                    combinedErrors && combinedErrors.availableOn
                      ? combinedErrors.availableOn
                      : ""
                  }
                />
                <FormSpacer />
                {created && (
                  <Typography variant="body1">Created at: {created}</Typography>
                )}
                <FormSpacer />
                <ControlledCheckbox
                  checked={this.state.isVisible}
                  label={i18n.t("Published", { context: "label" })}
                  name="isVisible"
                  onChange={this.handleChange}
                />
              </Grid>
            </Grid>
          </CardContent>
          <Toolbar className={classes.cardActions}>
            <Button
              variant="raised"
              color="primary"
              onClick={() => handleSubmit(this.state)}
            >
              {i18n.t("Submit", { context: "label" })}
            </Button>
          </Toolbar>
        </>
      );
    }
  }
);

export default PageUpdateFormComponent;
