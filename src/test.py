from src import k8s_manager

def main():

    a = k8s_manager.k8s_manager(None,'default',False)

    b = a.get_version(False)




if __name__ == '__main__':
    main()

