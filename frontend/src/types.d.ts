declare module '*.jsx' {
    const component: any;
    export default component;
  }
  
  declare module '*.js' {
    const value: any;
    export default value;
  }
  
  declare module './hooks/useAuth' {
    export const useAuth: any;
  }
  
  declare module './components/Auth/Login' {
    const Login: any;
    export default Login;
  }
  
  declare module './components/UserManagement/UserList' {
    const UserList: any;
    export default UserList;
  }
  
  declare module './components/UserManagement/UserForm' {
    const UserForm: any;
    export default UserForm;
  }