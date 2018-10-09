import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

interface SiteSettingsKeyDialogProps {}

const decorate = withStyles(theme => ({ root: {} }));
const SiteSettingsKeyDialog = decorate<SiteSettingsKeyDialogProps>(({ classes }) => <div />);
SiteSettingsKeyDialog.displayName = "SiteSettingsKeyDialog";
export default SiteSettingsKeyDialog;
