#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <pthread.h>

#define BUF_SIZE 300000
#define BUF_MOUSE 30
#define MAX_CLNT 2

int clnt_socks[MAX_CLNT];
int clnt_count = 0;

pthread_mutex_t mutx;

void *handle_clnt(void *arg);
void send_msg(char *msg, int len);
void send_mouse(char *mouse, int len);

int main(int argc, char *argv[])
{
    int serv_sock, clnt_sock;
    struct sockaddr_in serv_adr, clnt_adr;
    socklen_t clnt_adr_sz;
    pthread_t t_id;

    pthread_mutex_init(&mutx, NULL);

    serv_sock = socket(PF_INET, SOCK_STREAM, 0);
    memset(&serv_adr, 0, sizeof(serv_adr));
    serv_adr.sin_family = AF_INET;
    serv_adr.sin_addr.s_addr = htonl(INADDR_ANY);
    serv_adr.sin_port = htons(4205);

    if (bind(serv_sock, (struct sockaddr*)&serv_adr, sizeof(serv_adr)) == -1)
    {
        perror("bind() error");
        exit(EXIT_FAILURE);
    }

    if (listen(serv_sock, 5) == -1)
    {
        perror("listen() error");
        exit(EXIT_FAILURE);
    }

    while (1)
    {
        clnt_adr_sz = sizeof(clnt_adr);
        clnt_sock = accept(serv_sock, (struct sockaddr*)&clnt_adr, &clnt_adr_sz);

        pthread_mutex_lock(&mutx);
        clnt_socks[clnt_count++] = clnt_sock;
        pthread_mutex_unlock(&mutx);

        pthread_create(&t_id, NULL, handle_clnt, (void*)&clnt_sock);
        pthread_detach(t_id);
    }

    close(serv_sock);
    return 0;
}

void *handle_clnt(void *arg)
{
    int clnt_sock = *((int*)arg);
    int str_len = 0;
    char msg[BUF_SIZE];

    while ((str_len = read(clnt_sock, msg, sizeof(msg))) != 0)
        send_msg(msg, str_len);

    pthread_mutex_lock(&mutx);
    for (int i = 0; i < clnt_count; i++)
    {
        if (clnt_sock == clnt_socks[i])
        {
            while (i++ < clnt_count - 1)
                clnt_socks[i] = clnt_socks[i + 1];
            break;
        }
    }
    clnt_count--;
    pthread_mutex_unlock(&mutx);
    close(clnt_sock);
    return NULL;
}

void send_msg(char *msg, int len)
{
    pthread_mutex_lock(&mutx);
    for (int i = 0; i < clnt_count; i++)
        write(clnt_socks[i], msg, len);
    pthread_mutex_unlock(&mutx);
}
