import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

interface StaffPermissionsProps {}

const decorate = withStyles(theme => ({ root: {} }));
const StaffPermissions = decorate<StaffPermissionsProps>(({ classes }) => <div />);
StaffPermissions.displayName = "StaffPermissions";
export default StaffPermissions;
