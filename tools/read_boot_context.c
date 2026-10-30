/* Read-only chosen boot context accessor. Never opens an IOService user client. */
typedef unsigned int io_object_t;
typedef unsigned long CFTypeID;
typedef long CFIndex;
typedef const void *CFTypeRef;
extern int printf(const char *, ...);
extern void *dlopen(const char *, int);
extern void *dlsym(void *, const char *);
extern char *dlerror(void);

int main(void) {
    void *io = dlopen("/System/Library/Frameworks/IOKit.framework/Versions/A/IOKit", 2);
    if (!io) io = dlopen("/usr/lib/libIOKit.A.dylib", 2);
    if (!io) io = dlopen("/System/Library/Frameworks/IOKit.framework/IOKit", 2);
    if (!io) { printf("ERROR IOKit dlopen: %s\n", dlerror()); return 2; }
    void *cf = dlopen("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation", 2);
    if (!cf) { printf("ERROR CoreFoundation dlopen: %s\n", dlerror()); return 3; }
    io_object_t (*entryFromPath)(unsigned int, const char *) = dlsym(io, "IORegistryEntryFromPath");
    CFTypeRef (*property)(io_object_t, CFTypeRef, CFTypeRef, unsigned int) = dlsym(io, "IORegistryEntryCreateCFProperty");
    int (*objectRelease)(io_object_t) = dlsym(io, "IOObjectRelease");
    CFTypeRef (*stringCreate)(CFTypeRef, const char *, unsigned int) = dlsym(cf, "CFStringCreateWithCString");
    CFTypeID (*getTypeID)(CFTypeRef) = dlsym(cf, "CFGetTypeID");
    CFTypeID (*dataTypeID)(void) = dlsym(cf, "CFDataGetTypeID");
    CFIndex (*dataLength)(CFTypeRef) = dlsym(cf, "CFDataGetLength");
    const unsigned char *(*dataBytes)(CFTypeRef) = dlsym(cf, "CFDataGetBytePtr");
    void (*release)(CFTypeRef) = dlsym(cf, "CFRelease");
    if (!entryFromPath || !property || !objectRelease || !stringCreate ||
        !getTypeID || !dataTypeID || !dataLength || !dataBytes || !release) {
        printf("ERROR required read-only registry or CoreFoundation symbol unavailable\n"); return 4;
    }
    io_object_t entry = entryFromPath(0, "IODeviceTree:/chosen");
    if (!entry) { printf("ERROR IODeviceTree:/chosen unavailable\n"); return 5; }
    const char *names[2] = {"boot-nonce", "boot-manifest-hash"};
    const char *labels[2] = {"BOOT_NONCE", "BOOT_MANIFEST_HASH"};
    const CFIndex sizes[2] = {8, 20};
    unsigned char copied[2][20];
    for (int field = 0; field < 2; ++field) {
        CFTypeRef key = stringCreate((void *)0, names[field], 0x08000100U);
        if (!key) { objectRelease(entry); printf("ERROR cannot create property key\n"); return 6; }
        CFTypeRef value = property(entry, key, (void *)0, 0);
        release(key);
        if (!value) { objectRelease(entry); printf("ERROR chosen/%s property absent\n", names[field]); return 7; }
        if (getTypeID(value) != dataTypeID()) {
            release(value); objectRelease(entry); printf("ERROR chosen/%s is not CFData\n", names[field]); return 8;
        }
        CFIndex length = dataLength(value);
        if (length != sizes[field]) {
            release(value); objectRelease(entry);
            printf("ERROR chosen/%s length=%ld, expected %ld\n", names[field], length, sizes[field]); return 9;
        }
        const unsigned char *bytes = dataBytes(value);
        if (!bytes) { release(value); objectRelease(entry); printf("ERROR chosen/%s data pointer unavailable\n", names[field]); return 10; }
        for (CFIndex i = 0; i < length; ++i) copied[field][i] = bytes[i];
        release(value);
    }
    objectRelease(entry);
    for (int field = 0; field < 2; ++field) {
        printf("%s=", labels[field]);
        for (CFIndex i = 0; i < sizes[field]; ++i) printf("%02x", copied[field][i]);
        printf("\n");
    }
    return 0;
}
