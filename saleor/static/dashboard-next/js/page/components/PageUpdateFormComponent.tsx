import * as React from "react";
import TextField from "material-ui/TextField";
import Grid from "material-ui/Grid";
import { CardContent } from "material-ui/Card";
import Toolbar from "material-ui/Toolbar";
import Typography from "material-ui/Typography";
import Button from "material-ui/Button";
import CheckBox from "material-ui/CheckBox";
import { withStyles, WithStyles } from "material-ui/styles";

import { TypedPageDetailsQuery, pageDetailsQuery } from "../queries";
import i18n from "../../i18n";
import RichTextEditor from "../../components/RichTextEditor";
import FormSpacer from "../../components/FormSpacer";
import ControlledCheckbox from "../../components/ControlledCheckbox";

interface PageUpdateFormComponentState {
  title: string;
  slug: string;
  content: string;
  availableOn: string;
  isVisible: boolean;
}

interface PageUpdateFormComponentProps {
  handleSubmit(data: any);
  formInitialValues?: PageUpdateFormComponentState;
  created: string;
}

const decorate = withStyles(theme => ({
  cardActions: {
    flexDirection: "row-reverse" as "row-reverse"
  },
  addHelperTextPadding: {
    [theme.breakpoints.up("md")]: {
      paddingBottom: theme.spacing.unit * 2.5
    }
  }
}));

export const PageUpdateFormComponent = decorate(
  class PageUpdateFormUnstyledComponent extends React.Component<
    PageUpdateFormComponentProps &
      WithStyles<"cardActions" | "addHelperTextPadding">,
    PageUpdateFormComponentState
  > {
    static defaultState = {
      title: "",
      slug: "",
      content: "",
      availableOn: "",
      isVisible: false
    };

    constructor(props) {
      super(props);
      this.state = {
        ...PageUpdateFormUnstyledComponent.defaultState,
        ...props.formInitialValues
      };
    }

    handleChange = event => {
      console.log(event.target);
      this.setState({ [event.target.name]: event.target.value });
    };

    render() {
      const { created, formInitialValues, handleSubmit, classes } = this.props;
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
                  className={classes.addHelperTextPadding}
                  fullWidth
                />
                <FormSpacer />
                <RichTextEditor
                  defaultValue={this.state.content}
                  name="content"
                  label={i18n.t("Content", { context: "object" })}
                  helperText={i18n.t(
                    "Select text to enable text-formatting tools.",
                    {
                      context: "object"
                    }
                  )}
                  onChange={this.handleChange}
                  fullWidth
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <TextField
                  name="slug"
                  label={i18n.t("Slug", { context: "object" })}
                  defaultValue={this.state.slug}
                  helperText={i18n.t("Slug is being used to create page URL", {
                    context: "object"
                  })}
                  onChange={this.handleChange}
                  fullWidth
                />
                <FormSpacer />
                <TextField
                  name="availableOn"
                  label={i18n.t("Available on", { context: "label" })}
                  type="date"
                  defaultValue={formInitialValues.availableOn}
                  onChange={this.handleChange}
                  InputLabelProps={{
                    shrink: true
                  }}
                />
                <FormSpacer />
                <Typography variant="body1">Created at: {created}</Typography>
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
