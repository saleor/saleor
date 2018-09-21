import { withStyles } from "@material-ui/core/styles";
import * as React from "react";

interface StaffStatusProps {}

const decorate = withStyles(theme => ({ root: {} }));
const StaffStatus = decorate<StaffStatusProps>(({ classes }) => <div />);
StaffStatus.displayName = "StaffStatus";
export default StaffStatus;
