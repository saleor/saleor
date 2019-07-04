import { useContext } from "react";

import { UserContext } from "../auth";

function useUser() {
  const user = useContext(UserContext);
  return user;
}
export default useUser;
